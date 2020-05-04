import os
import jinja2
from .utils import create_folder_struct, get_folder_struct
from .ippack import ippack
from pygears import registry
from pygears.typing import Queue, typeof
from pygears.core.gear import InSig
from pygears.hdl import hdlgen
from pygears.hdl.templenv import get_port_intfs
from pygears.hdl.templenv import TemplateEnv
from pygears.typing.math import ceil_chunk, ceil_div, ceil_pow2
from pygears.util.fileio import save_file
from pygears.hdl.intfs.generate import generate as generate_wrap, get_axi_conf
from .drvgen import drvgen

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


def generate(top, outdir, lang, intfdef, prjdir):
    dirs = get_folder_struct(outdir)
    create_folder_struct(dirs)

    drv_files = []

    hdlgen(top, outdir=dirs['hdl'], wrapper=False, copy_files=True, lang=lang)

    modinst = registry('svgen/map')[top]

    sigs = []
    for s in top.signals.values():
        if s.name == 'clk':
            sigs.append(InSig('aclk', 1))
        elif s.name == 'rst':
            sigs.append(InSig('aresetn', 1))
        else:
            sigs.append(s)

    drv_files = drvgen(top, intfdef, dirs['driver'])

    wrp, files = generate_wrap(top, intfdef)

    ippack(
        top,
        dirs,
        intfdef=intfdef,
        lang=lang,
        prjdir=prjdir,
        files=files,
        drv_files=drv_files)

    preproc_hdl(dirs, mapping=default_preproc)

    save_file(f'wrap_{os.path.basename(modinst.file_basename)}', dirs['hdl'], wrp)
