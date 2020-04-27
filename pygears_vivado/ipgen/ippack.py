import os
import jinja2
import glob
import shutil
from pygears.definitions import LIB_VLIB_DIR

from pygears import registry
from pygears.util.fileio import save_file
from pygears.hdl.intfs.generate import get_axi_conf

from . import SVVivModuleInst


# def ippack(top, dirs, lang, prjdir, drv_files, axi_port_cfg):
def ippack(top, dirs, intfdef, lang, prjdir, files, drv_files):

    hdlgen_map = registry(f'{lang}gen/map')
    modinst = hdlgen_map[top]
    wrap_name = f'wrap_{modinst.module_name}'

    for fn in files:
        try:
            shutil.copy(os.path.join(LIB_VLIB_DIR, fn), dirs['hdl'])
        except shutil.SameFileError:
            pass

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

    c_files = []
    for f in drv_files:
        if f[-3:] in ['mdd', 'tcl']:
            continue

        if os.path.basename(f) == 'Makefile':
            continue

        c_files.append(os.path.relpath(f, dirs['root']))

    context = {
        'prjdir': prjdir,
        'hdldir': dirs['hdl'],
        'ipdir': dirs['root'],
        'ip_name': top.basename,
        'wrap_name': wrap_name,
        'files': files,
        'drv_files': c_files,
        'axi_port_cfg': intfdef,
        'description': '"PyGears {} IP"'.format(top.basename)
    }

    base_addr = os.path.dirname(__file__)
    env = jinja2.Environment(
        extensions=['jinja2.ext.loopcontrols'],
        loader=jinja2.FileSystemLoader([base_addr, os.path.dirname(base_addr)]),
        trim_blocks=True,
        lstrip_blocks=True)
    env.globals.update(zip=zip)

    tmplt = 'axipack.j2'

    env.globals.update(os=os)

    res = env.get_template(tmplt).render(context)
    save_file('ippack.tcl', dirs['script'], res)
