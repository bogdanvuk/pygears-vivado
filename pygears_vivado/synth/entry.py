import runpy
import os
import json
import tempfile

from pygears.definitions import CACHE_DIR
from pygears import reg, find
from pygears.entry import cmd_register
from pygears.util.fileio import get_main_script
from pygears.hdl.synth import SynthPlugin
from pygears.conf.custom_settings import load_rc

from . import run
from .generate import generate as generate_synth
# from .makefile import makefile
from .reports import parse_utilization, parse_timing


def synth(top,
          design=None,
          outdir=None,
          include=None,
          lang='sv',
          generate=True,
          build=True,
          util=False,
          timing=False,
          prjdir=None):

    if reg['vivado/synth/lock']:
        return

    if design is None:
        design = get_main_script()

    if design is not None:
        design = os.path.abspath(os.path.expanduser(design))

    if isinstance(top, str):
        top_mod = find(top)
    else:
        top_mod = top

    if outdir is None:
        outdir = os.path.join(reg['vivado/iplib'], top.basename)

    os.makedirs(outdir, exist_ok=True)

    # makefile(
    #     top,
    #     design,
    #     outdir,
    #     lang=lang,
    #     generate=generate,
    #     build=build,
    #     include=include,
    #     prjdir=prjdir)

    if not generate:
        return

    if top_mod is None:
        reg['vivado/synth/lock'] = True
        load_rc('.pygears', os.path.dirname(design))
        runpy.run_path(design)
        reg['vivado/synth/lock'] = False
        top_mod = find(top)

    if top_mod is None:
        raise Exception(
            f'Module "{top}" specified as a IP core top level module, not found in the design "{design}"'
        )

    if prjdir is None:
        prjdir = tempfile.mkdtemp()

    if include is None:
        include = []

    include += reg[f'{lang}gen/include']

    generate_synth(top_mod, outdir, lang, util, timing, prjdir)

    if build:
        ret = run(os.path.join(outdir, 'synth.tcl'))
        if ret != 0:
            raise Exception('Vivado build error')

    report = {}
    if util:
        report['util'] = parse_utilization(f'{prjdir}/utilization.txt')

    if timing:
        report['path_delay'] = parse_timing(f'{prjdir}/timing.txt')

    return report


class VivadoSynthPlugin(SynthPlugin):
    @classmethod
    def bind(cls):
        conf = cmd_register(['synth', 'vivado'], synth, aliases=['viv'], derived=True)

        reg['vivado/synth/lock'] = False

        conf['parser'].add_argument('--prjdir', type=str)
        conf['parser'].add_argument('--util', action='store_true')
        conf['parser'].add_argument('--timing', action='store_true')
