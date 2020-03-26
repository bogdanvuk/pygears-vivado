import os
import jinja2
import glob

from pygears import registry
from pygears.util.fileio import save_file

from . import SVVivModuleInst


def ippack(top, dirs, lang, prjdir, drv_files, axi_port_cfg):

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
        'ports': axi_port_cfg,
        'bram_params': {},
        'description': '"PyGears {} IP"'.format(top.basename)
    }

    base_addr = os.path.dirname(__file__)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([base_addr, os.path.dirname(base_addr)]),
        trim_blocks=True,
        lstrip_blocks=True)
    env.globals.update(zip=zip)

    if not axi_port_cfg:
        tmplt = 'ippack.j2'
    else:
        tmplt = 'axipack.j2'

        for name, cfg in axi_port_cfg.items():
            if cfg['type'] in ['bram', 'bram.req']:
                context['bram_params'][name] = {
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

        context['dma_params']['c_include_mm2s'] = 0
        context['dma_params']['c_include_s2mm'] = 0

        env.globals.update(os=os)

    res = env.get_template(tmplt).render(context)
    save_file('ippack.tcl', dirs['script'], res)
