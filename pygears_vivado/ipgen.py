import os
import json
from copy import deepcopy
import glob
import tempfile
import inspect
import shutil
import jinja2

from pygears.definitions import CACHE_DIR
from pygears import registry, config
from pygears.core.gear import InSig
from pygears.util.fileio import save_if_changed, save_file, copy_file
from pygears.core.hier_node import HierYielderBase
from pygears.hdl import list_hdl_files, hdlgen, find_rtl
from pygears.hdl.ipgen import IpgenPlugin
from pygears.hdl.templenv import TemplateEnv
from pygears.hdl.sv.generate import SVTemplateEnv
from pygears.hdl.v.generate import VTemplateEnv
from pygears.typing.math import ceil_chunk, ceil_div, ceil_pow2
from pygears.typing.visitor import TypingVisitorBase
from pygears.typing import Uint, Int, Bool, Queue, typeof, Integral, Fixp, Tuple

from .vivmod import SVVivModuleInst
from .intf import run

default_preproc = {
    ".consumer": ".slave",
    ".producer": ".master",
    "modport consumer": "modport slave",
    "modport producer": "modport master"
}

wrap_preproc = {
    '_valid': '_tvalid',
    '_ready': '_tready',
    '_data': '_tdata',
    'input clk': 'input aclk',
    '.clk(clk)': '.clk(aclk)',
    'input rst': 'input aresetn',
    '.rst(rst)': '.rst(~aresetn)'
}


class TypeVisitor(TypingVisitorBase):
    def __init__(self):
        self.hier = []
        self.offset = 0
        self.regs = []
        self.ctrl = []

    def func_reg(self, path, offset, width, type_):
        self.regs.append(
            {
                'path': path.copy(),
                'offset': offset,
                'width': width,
                'ctrl': deepcopy(self.ctrl),
                'type': type_
            })

    def visit_queue(self, type_, field):
        self.visit(type_[0], 'data')
        self.func_reg(self.hier + ['eot'], self.offset, int(type_[1:]), type_[1:])
        self.offset += int(type_[1:])

    def visit_union(self, type_, field):
        start_offset = self.offset
        for i, (t, f) in enumerate(zip(type_.types(), type_.fields)):
            self.offset = start_offset
            self.ctrl.append({'val': i, 'path': self.hier + ['ctrl']})
            self.visit(t, f)
            self.ctrl.pop()

        self.offset = start_offset + int(type_[0])
        self.func_reg(self.hier.copy() + ['ctrl'], self.offset, int(type_[1]), type_[1])
        self.offset += int(type_[1])

    def visit(self, type_, field=None):
        if field:
            self.hier.append(field)

        self.func_reg(self.hier, self.offset, int(type_), type_)

        if typeof(type_, Integral):
            self.offset += int(type_)
        else:
            super().visit(type_, field)

        if self.hier:
            self.hier.pop()


def drvgen(top, dirs, dma_port_cfg):
    # out_port = list(top.svgen.out_ports())[0]
    cmd_type = top.in_ports[0].dtype
    dout_type = top.out_ports[0].dtype

    v = TypeVisitor()
    v.visit(cmd_type)
    regs = v.regs
    regs = list(filter(lambda r: r['width'] > 0, regs))
    for r in regs:
        r['path'] = '_'.join(r['path'])
        if r['ctrl']:
            r['ctrl'][0]['path'] = '_'.join(r['ctrl'][0]['path'])

    drv_dir = os.path.join(dirs['driver'], f'{top.basename}_v1_0')

    src_dir = os.path.join(drv_dir, 'src')
    src_relative_dir = os.path.join('driver', f'{top.basename}_v1_0', 'src')
    data_dir = os.path.join(drv_dir, 'data')

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        trim_blocks=True,
        lstrip_blocks=True)

    env.globals.update(repr=repr, len=len, typeof=typeof, Fixp=Fixp)
    drv_files = []

    content = env.get_template("drivers/drvgen_c.j2").render(
        regs=regs,
        module_name=top.basename,
        cfg_words_num=ceil_div(int(cmd_type), 32),
        dout_words_num=ceil_div(int(dout_type), 32),
        dma_ports=dma_port_cfg,
        cmd_type=cmd_type)

    save_file(f'{top.basename}.c', src_dir, content)
    drv_files.append(os.path.join(src_relative_dir, f'{top.basename}.c'))

    content = env.get_template('drivers/drvgen_h.j2').render(
        regs=regs, module_name=top.basename, cmd_type=cmd_type)
    save_file(top.basename + '.h', src_dir, content)
    drv_files.append(os.path.join(src_relative_dir, f'{top.basename}.h'))

    content = env.get_template('drivers/drvgen_mdd.j2').render(module_name=top.basename)
    save_file(top.basename + '.mdd', data_dir, content)

    content = env.get_template('drivers/drvgen_tcl.j2').render(module_name=top.basename)
    save_file(top.basename + '.tcl', data_dir, content)

    copy_file(
        'Makefile', src_dir,
        os.path.join(os.path.dirname(__file__), 'drivers', 'Makefile'))

    axi_drv_dir = os.path.join(os.path.dirname(__file__), 'drivers', 'axidma_v9_8')
    for f in os.listdir(axi_drv_dir):
        copy_file(f, src_dir, os.path.join(axi_drv_dir, f))
        drv_files.append(os.path.join(src_relative_dir, f))

    return drv_files


def ippack_script(top, dirs, lang, prjdir, drv_files, dma_port_cfg):
    base_addr = os.path.dirname(__file__)

    hdlgen_map = registry(f'{lang}gen/map')
    modinst = hdlgen_map[top]
    wrap_name = f'wrap_{modinst.module_name}'

    files = [dirs['hdl']]
    for rtl, mod in hdlgen_map.items():
        if isinstance(mod, SVVivModuleInst):
            for f in mod.files:
                try:
                    os.remove(os.path.join(dirs['hdl'], os.path.basename(f)))
                except FileNotFoundError:
                    pass

            xci = glob.glob(f'{mod.ipdir}/*.xci')[0]
            # xci_local = os.path.join(dirs['hdl'], os.path.basename(xci))
            # shutil.copyfile(xci, xci_local)
            if xci not in files:
                files.append(xci)

    context = {
        'prjdir': prjdir,
        'hdldir': dirs['hdl'],
        'ipdir': dirs['root'],
        'ip_name': top.basename,
        'wrap_name': wrap_name,
        'files': files,
        'drv_files': drv_files,
        'ports': dma_port_cfg,
        'description': '"PyGears {} IP"'.format(top.basename)
    }

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(base_addr), trim_blocks=True, lstrip_blocks=True)
    env.globals.update(zip=zip)

    if not dma_port_cfg:
        tmplt = 'ippack.j2'
    else:
        tmplt = 'axipack.j2'
        if dma_port_cfg['din']['type'] == 'bram':
            context['bram_params'] = {
                'protocol': 'AXI4',
                'single_port_bram': 1,
                'ecc_type': 0
            }

        context['dma_params'] = {
            'c_include_sg': 0,
            'c_sg_include_stscntrl_strm': 0,
            'c_mm2s_burst_size': 8,
            'c_s2mm_burst_size': 8
        }

        if dma_port_cfg['din']['type'] == 'axi':
            context['dma_params'].update(
                c_m_axi_mm2s_data_width=dma_port_cfg['din']['width'],
                c_m_axis_mm2s_tdata_width=dma_port_cfg['din']['width'])
        else:
            context['dma_params']['c_include_mm2s'] = 0

        if dma_port_cfg['dout']['type'] == 'axi':
            context['dma_params'].update(
                c_m_axi_s2mm_data_width=dma_port_cfg['dout']['width'],
                c_s_axis_s2mm_tdata_width=dma_port_cfg['dout']['width'])
        else:
            context['dma_params']['c_include_s2mm'] = 0

        env.globals.update(os=os)

    res = env.get_template(tmplt).render(context)
    save_file('ippack.tcl', dirs['script'], res)


def makefile_script(top, design, dirs, lang, hdl_include, copy, intf, prjdir):

    seen = set()
    seen_add = seen.add
    py_files = [x for x in py_files_enum(top) if not (x in seen or seen_add(x))]

    context = {
        'py_sources': sorted(py_files),
        'ip_dir': dirs['root'],
        'ip_component_fn': os.path.join(dirs['root'], 'component.xml'),
        'hdl_include_path': [f'-I {p}' for p in hdl_include],
        'design_path': design,
        'top_path': top.name,
        'lang': lang,
        'copy': copy,
        'intf': json.dumps(intf),
        'prjdir': prjdir
    }

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        trim_blocks=True,
        lstrip_blocks=True)
    env.globals.update(zip=zip)

    res = env.get_template('ipgen_makefile.j2').render(context)

    save_if_changed('Makefile', dirs['root'], res)


def get_folder_struct(outdir):
    dirs = {n: os.path.join(outdir, n) for n in ['hdl', 'script', 'driver']}
    dirs['root'] = outdir

    return dirs


def create_folder_struct(dirs):
    for k, d in dirs.items():
        os.makedirs(d, exist_ok=True)


def purge_folder_struct(dirs):
    for k, d in dirs.items():
        if k != 'root':
            shutil.rmtree(d, ignore_errors=True)

        os.makedirs(d, exist_ok=True)


class HdlNodeYielder(HierYielderBase):
    def __init__(self, lang):
        self.lang = lang

    def RTLNode(self, node):
        gen_map = registry(f'{self.lang}gen/map')
        yield gen_map[node]


class RtlNodeYielder(HierYielderBase):
    def RTLNode(self, node):
        yield node


def _py_file_enum_raw(rtlnode):
    for node in RtlNodeYielder().visit(rtlnode):
        yield os.path.abspath(inspect.getfile(node.gear.func))

    for t in node.gear.trace:
        yield os.path.abspath(inspect.getframeinfo(t[0]).filename)


def py_files_enum(rtlnode):
    for fn in _py_file_enum_raw(rtlnode):
        if '<decorator-gen' not in fn:
            yield fn


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


def ipgen(
        top,
        design,
        outdir=None,
        include=[],
        lang='sv',
        build=False,
        copy=True,
        makefile=True,
        intf='["axis", "axis"]',
        prjdir=None):

    if isinstance(intf, str):
        intf = json.loads(intf)

    if outdir is None:
        rtl_top = find_rtl(top)
        outdir = os.path.join(config['vivado/iplib'], rtl_top.basename)

    if prjdir is None:
        prjdir = tempfile.mkdtemp()

    dirs = get_folder_struct(outdir)
    os.makedirs(dirs['root'], exist_ok=True)

    include += config[f'{lang}gen/include']

    rtlnode = hdlgen(
        top,
        outdir=dirs['hdl'],
        wrapper=False,
        generate=not makefile,
        copy_files=True,
        language=lang)

    if makefile:
        makefile_script(
            rtlnode,
            design=design,
            dirs=dirs,
            lang=lang,
            hdl_include=include,
            copy=copy,
            intf=intf,
            prjdir=prjdir)
    else:
        create_folder_struct(dirs)

        drv_files = []
        dma_port_cfg = {}
        for p, name, i in zip([rtlnode.in_ports[0], rtlnode.out_ports[0]],
                              ['din', 'dout'], intf):
            dtype = p.dtype
            w_data = int(dtype)
            w_eot = 0
            w_addr = 0
            if typeof(dtype, Queue):
                w_data = int(dtype.data)
                w_eot = int(dtype.eot)
                width = ceil_chunk(ceil_pow2(int(w_data)), 32)
            elif i == "bram" and typeof(dtype, Tuple):
                w_addr = len(dtype[0])
                w_data = len(dtype[1])
                width = ceil_chunk(ceil_pow2(int(w_data)), 32)
            else:
                width = ceil_chunk(w_data, 8)

            port_cfg = {
                'width': width,
                'w_data': w_data,
                'w_eot': w_eot,
                'w_addr': w_addr,
                'name': name,
                'type': i
            }
            dma_port_cfg[name] = port_cfg

        if intf[0] == 'axi' or intf[1] == 'axi':
            drv_files = drvgen(rtlnode, dirs, dma_port_cfg=dma_port_cfg)

        ippack_script(
            rtlnode,
            dirs,
            lang=lang,
            prjdir=prjdir,
            drv_files=drv_files,
            dma_port_cfg=dma_port_cfg)

        preproc_hdl(dirs, mapping=default_preproc)

        modinst = registry('svgen/map')[rtlnode]

        sigs = []
        for s in modinst.node.params['signals']:
            if s.name == 'clk':
                sigs.append(InSig('aclk', 1))
            elif s.name == 'rst':
                sigs.append(InSig('aresetn', 1))
            else:
                sigs.append(s)

        intfs = list(modinst.port_configs)
        for i in intfs:
            dtype = i['type']
            w_data = i['width']
            w_eot = 0
            if typeof(dtype, Queue):
                w_data = int(dtype.data)
                w_eot = int(dtype.eot)

            i['w_data'] = w_data
            i['w_eot'] = w_eot

        context = {
            'wrap_module_name': f'wrap_{modinst.module_name}',
            'module_name': modinst.module_name,
            'inst_name': modinst.inst_name,
            'intfs': intfs,
            'sigs': sigs,
            'param_map': modinst.params
        }

        tenv = TemplateEnv(os.path.dirname(__file__))

        # if intf[0] == 'axis' and intf[1] == 'axis':
        #     tmplt = 'ip_hdl_wrap.j2'
        # else:
        tmplt = 'ip_axi_hdl_wrap.j2'
        tenv.jenv.globals.update(
            ceil_pow2=ceil_pow2, ceil_div=ceil_div, ceil_chunk=ceil_chunk)

        context['ports'] = dma_port_cfg

        if intf[1] == 'axis':
            context['pg_clk'] = f'{intfs[1]["name"]}_aclk'
        elif intf[1] == 'axi':
            context['pg_clk'] = 's_axi_lite_aclk'

        wrp = tenv.render_local(__file__, tmplt, context)
        save_file(f'wrap_{os.path.basename(modinst.file_name)}', dirs['hdl'], wrp)

        if build:
            run(os.path.join(dirs['script'], 'ippack.tcl'))


class VivadoIpgenPlugin(IpgenPlugin):
    @classmethod
    def bind(cls):
        config.define('vivado/iplib', default=os.path.join(CACHE_DIR, 'vivado', 'iplib'))
        config['ipgen/backend']['vivado'] = ipgen
        vivparser = config['ipgen/subparser'].add_parser(
            'vivado', parents=[config['ipgen/baseparser']])

        vivparser.add_argument('--intf', type=str, default='axis,axis')

        vivparser.add_argument('--prjdir', type=str)
