import runpy
import os
import json
import tempfile

from pygears.definitions import CACHE_DIR
from pygears import registry, config, find, bind, safe_bind
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
    prjdir=None):

    if registry('vivado/ipgen/lock'):
        return

    if design is None:
        design = get_main_script()

    design = os.path.abspath(os.path.expanduser(design))

    if outdir is None:
        outdir = os.path.join(
            config['vivado/iplib'], top if isinstance(top, str) else top.basename)

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
        bind('vivado/ipgen/lock', True)
        load_rc('.pygears', os.path.dirname(design))
        runpy.run_path(design)
        bind('vivado/ipgen/lock', False)
        top_mod = find(top)

    if top_mod is None:
        raise Exception(
            f'Module "{top}" specified as a IP core top level module, not found in the design "{design}"')

    if prjdir is None:
        prjdir = tempfile.mkdtemp()

    if include is None:
        include = []

    include += config[f'{lang}gen/include']

    if isinstance(intf, str):
        intf = json.loads(intf)
    # elif intf is None:
    #     intf = ('axis', ) * (len(top_mod.in_ports) + len(top_mod.out_ports))
    # elif isinstance(intf, dict):
    #     intf = tuple(intf[p.basename] for p in top_mod.in_ports + top_mod.out_ports)

    # if len(intf) != (len(top_mod.in_ports) + len(top_mod.out_ports)):
    #     raise Exception(
    #         f"{len(intf)} interface types supplied {intf}, but '{top_mod.name}' has "
    #         f"{len(top_mod.in_ports) + len(top_mod.out_ports)} ports")
    intfdef = get_axi_conf(top_mod, intf)
    generate_ip(top_mod, outdir, lang, intfdef, prjdir)

    if build:
        ret = run(os.path.join(outdir, 'script', 'ippack.tcl'))
        if ret != 0:
            raise Exception('Vivado build error')


class VivadoIpgenPlugin(IpgenPlugin):
    @classmethod
    def bind(cls):
        conf = cmd_register(['ipgen', 'vivado'], ipgen, aliases=['viv'], derived=True)

        config.define('vivado/iplib', default=os.path.join(CACHE_DIR, 'vivado', 'iplib'))

        safe_bind('vivado/ipgen/lock', False)

        conf['parser'].add_argument('--intf', type=str)

        conf['parser'].add_argument('--prjdir', type=str)
