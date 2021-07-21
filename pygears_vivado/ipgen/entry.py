import runpy
import os
import json
import tempfile

from pygears.definitions import CACHE_DIR
from pygears import reg, find
from pygears.entry import cmd_register
from pygears.util.fileio import get_main_script
from pygears.hdl.ipgen import IpgenPlugin
from pygears.conf.custom_settings import load_rc
from pygears.hdl.intfs.axi import get_axi_conf

from . import run
from .generate import generate as generate_ip
from .makefile import makefile


def ipgen(
    top,
    design,
    outdir=None,
    include=None,
    lang='sv',
    generate=True,
    build=True,
    intf=None,
    prjdir=None,
    presynth=False,
    rst=True,
):

    if reg['vivado/ipgen/lock']:
        return

    if design is None:
        design = get_main_script()

    design = os.path.abspath(os.path.expanduser(design))

    if outdir is None:
        outdir = os.path.join(
            reg['vivado/iplib'], top if isinstance(top, str) else top.basename)

    os.makedirs(outdir, exist_ok=True)

    makefile(
        top,
        design,
        outdir,
        lang=lang,
        generate=generate,
        build=build,
        include=include,
        intf=intf,
        prjdir=prjdir)

    if not generate:
        return

    if isinstance(top, str):
        top_mod = find(top)
    else:
        top_mod = top

    if top_mod is None:
        reg['vivado/ipgen/lock'] = True
        load_rc('.pygears', os.path.dirname(design))
        runpy.run_path(design)
        reg['vivado/ipgen/lock'] = False
        top_mod = find(top)

    if top_mod is None:
        raise Exception(
            f'Module "{top}" specified as a IP core top level module, not found in the design "{design}"')

    if prjdir is None:
        prjdir = tempfile.mkdtemp()

    if include is None:
        include = []

    include += reg[f'{lang}gen/include']

    if isinstance(intf, str):
        intf = json.loads(intf)

    if not intf:
        intf = {}
        for p in top_mod.in_ports + top_mod.out_ports:
            intf[p.basename] = 'axis'

    intfdef = get_axi_conf(top_mod, intf)
    generate_ip(top_mod, outdir, lang, intfdef, prjdir, presynth=presynth, rst=rst)

    if build:
        ret = run(os.path.join(outdir, 'script', 'ippack.tcl'))
        if ret != 0:
            raise Exception('Vivado build error')


class VivadoIpgenPlugin(IpgenPlugin):
    @classmethod
    def bind(cls):
        conf = cmd_register(['ipgen', 'vivado'], ipgen, aliases=['viv'], derived=True)

        reg.confdef('vivado/iplib', default=os.path.join(CACHE_DIR, 'vivado', 'iplib'))

        reg['vivado/ipgen/lock'] = False

        conf['parser'].add_argument('--intf', type=str)
        conf['parser'].add_argument('--presynth', '-p', action='store_false')

        conf['parser'].add_argument('--prjdir', type=str)
