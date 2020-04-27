import os
import jinja2
from .utils import create_folder_struct, get_folder_struct
from .axi import get_axi_conf
from .ippack import ippack
from pygears import registry
from pygears.typing import Queue, typeof
from pygears.core.gear import InSig
from pygears.hdl import hdlgen
from pygears.hdl.templenv import get_port_intfs
from pygears.hdl.templenv import TemplateEnv
from pygears.typing.math import ceil_chunk, ceil_div, ceil_pow2
from pygears.util.fileio import save_file
from . import axi_intfs

default_preproc = {
    ".consumer": ".slave",
    ".producer": ".master",
    "modport consumer": "modport slave",
    "modport producer": "modport master"
}


def preproc_file(fn, mapping):
    with open(fn, 'r') as content_file:
        content = content_file.read()

    for k, v in mapping.items():
        content = content.replace(k, v)

    with open(fn, 'w') as content_file:
        content_file.write(content)


def preproc_hdl(dirs, mapping):
    for fn in os.listdir(dirs['hdl']):
        fn = os.path.join(dirs['hdl'], fn)
        preproc_file(fn, mapping)


def generate(top, outdir, lang, intf, prjdir):
    dirs = get_folder_struct(outdir)
    create_folder_struct(dirs)

    drv_files = []
    axi_port_cfg = get_axi_conf(top, intf)

    hdlgen(top, outdir=dirs['hdl'], wrapper=False, copy_files=True, lang=lang)

    ippack(
        top,
        dirs,
        lang=lang,
        prjdir=prjdir,
        drv_files=drv_files,
        axi_port_cfg=axi_port_cfg)

    preproc_hdl(dirs, mapping=default_preproc)

    modinst = registry('svgen/map')[top]

    sigs = []
    for s in top.signals.values():
        if s.name == 'clk':
            sigs.append(InSig('aclk', 1))
        elif s.name == 'rst':
            sigs.append(InSig('aresetn', 1))
        else:
            sigs.append(s)

    intfs = {p['name']: p for p in get_port_intfs(top)}

    for i in intfs.values():
        dtype = i['type']
        w_data = i['width']
        w_eot = 0
        if typeof(dtype, Queue):
            w_data = int(dtype.data)
            w_eot = int(dtype.eot)

        i['w_data'] = w_data
        i['w_eot'] = w_eot

    defs = []
    for name, p in axi_port_cfg.items():
        if p['type'] in ['bram', 'bram.req']:
            if p['direction'] == 'in':
                pdefs = axi_intfs.port_def(
                    axi_intfs.AXI_SLAVE,
                    name,
                    waddr=p['w_addr'] + 2,  # Lower 2 bits are truncated for 4 byte bus
                    wdata={
                        'wdata': 32,
                        'wstrb': 4
                    },
                    bresp=True,
                    raddr=32,
                    rdata=32)
        elif p['type'] == 'axis':
            if p['direction'] == 'in':
                tmplt = axi_intfs.AXIS_SLAVE
            else:
                tmplt = axi_intfs.AXIS_MASTER

            pdefs = axi_intfs.port_def(tmplt, name, data=p['width'], last=p['w_eot'] > 0)

        defs.extend(pdefs)

    context = {
        'wrap_module_name': f'wrap_{modinst.module_name}',
        'module_name': modinst.module_name,
        'inst_name': modinst.inst_name,
        'intfs': intfs,
        'sigs': sigs,
        'param_map': modinst.params,
        'port_def': defs,
        'ports': axi_port_cfg
    }

    context['pg_clk'] = 'aclk'
    tmplt = 'ip_axi_hdl_wrap.j2'

    base_addr = os.path.dirname(__file__)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([base_addr, os.path.dirname(base_addr)]),
        trim_blocks=True,
        lstrip_blocks=True)

    env.globals.update(
        zip=zip,
        ceil_pow2=ceil_pow2,
        ceil_div=ceil_div,
        ceil_chunk=ceil_chunk,
        axi_intfs=axi_intfs)

    wrp = env.get_template(tmplt).render(context)
    save_file(f'wrap_{os.path.basename(modinst.file_basename)}', dirs['hdl'], wrp)
