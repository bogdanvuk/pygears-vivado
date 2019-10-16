import os
import json
import hashlib
import glob
import shutil
import tempfile
from pygears import config, find
from pygears.definitions import CACHE_DIR
from pygears.hdl.templenv import TemplateEnv
from pygears_vivado.intf import run

qrange_mux_str = '''
create_project -force prj_ippack {{prjdir}}

add_files -norecurse {{hdldir}}
set_property top wrap_{{ip_name}} [current_fileset]
update_compile_order -fileset sources_1
'''

from pygears import gear


@gear
def axi_ethernetlite():
    pass


def load_jenv():
    jenv = TemplateEnv(os.path.dirname(__file__))
    jenv.snippets = jenv.load(jenv.basedir, 'snippet.j2').module
    return jenv


def prjgen(name, files, prjdir, top=None, part=None):
    jenv = load_jenv()
    return jenv.snippets.prjgen(name, prjdir, files, part, top)


def ipdir(top, resdir=None, **kwds):
    if isinstance(top, str):
        top = find(top)

    if resdir is None:
        resdir = os.path.join(config['results-dir'], 'ip')

    params = top.explicit_params
    ipname = top.definition.__name__

    hsh_name = hashlib.sha1(
        (ipname +
         json.dumps(params, sort_keys=True)).encode()).hexdigest()[-8:]

    ipinst = f'{ipname}_{hsh_name}'
    return os.path.join(resdir, ipinst)


def ipinst(top, resdir=None):
    if isinstance(top, str):
        top = find(top)

    if resdir is None:
        resdir = os.path.join(CACHE_DIR, 'vivado', 'ipinst')

    prjdir = tempfile.mkdtemp()

    os.makedirs(resdir, exist_ok=True)
    params = {k: v for k, v in top.explicit_params.items() if k[0] != '_'}
    ipname = top.definition.__name__

    hsh_name = hashlib.sha1(
        (ipname +
         json.dumps(params, sort_keys=True)).encode()).hexdigest()[-8:]

    ipinst = f'{ipname}_{hsh_name}'
    ipdir = os.path.join(resdir, ipinst)

    if glob.glob(os.path.join(ipdir, 'synth', f'{ipinst}.*')):
        return ipdir

    tclpath = os.path.join(prjdir, 'ippack.tcl')

    with open(tclpath, 'w') as f:
        f.write(load_jenv().snippets.ip_inst(ipinst, ipname, resdir, prjdir,
                                             params))

    ret = run(tclpath)
    if ret:
        shutil.rmtree(ipdir)
        raise Exception(f"Vivado build failed with code: {ret}")

    return ipdir
