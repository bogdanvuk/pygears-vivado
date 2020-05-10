import jinja2
import sys
import os
import shutil

from subprocess import DEVNULL, Popen
from pygears.sim import sim_log
from pygears.definitions import ROOT_DIR
from pygears.util.fileio import save_file

from pygears import reg
from pygears.sim.extens.svsock import SVSockPlugin, CosimulatorUnavailable


def xsim(outdir=None, makefile=True, files=None, includes=None, batch=True, seed=None):
    if not makefile and not shutil.which('xsim'):
        raise CosimulatorUnavailable

    dpi_path = os.path.abspath(os.path.join(ROOT_DIR, 'sim', 'dpi'))
    context = {
        'dti_verif_path': dpi_path,
        'outdir': os.path.abspath(outdir),
        'top_name': 'top',
        'files': files,
        'includes': includes,
    }

    base_addr = os.path.dirname(__file__)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(base_addr), trim_blocks=True, lstrip_blocks=True)

    res = env.get_template('run_xsim.j2').render(context)
    fname = save_file('run_xsim.sh', outdir, res)
    os.chmod(fname, 0o777)

    kwds = {
        'batch': batch,
        'seed': seed if seed is not None else reg["sim/rand_seed"]
    }

    if makefile:
        sim_log().info(
            f"Waiting for manual XSim invocation. Run script: {fname}...")

        return None

    args = ' '.join(
        f'-{k} {v if not isinstance(v, bool) else ""}' for k, v in kwds.items()
        if not isinstance(v, bool) or v)

    # stdout = None
    stdout = DEVNULL

    sim_log().info(f'Starting XSim...')

    return Popen(
        [f'./run_xsim.sh'] + args.split(' '), stdout=stdout, stderr=stdout, cwd=outdir)


class VivadoSVSockPlugin(SVSockPlugin):
    @classmethod
    def bind(cls):
        reg['sim/svsock/backend']['xsim'] = xsim
