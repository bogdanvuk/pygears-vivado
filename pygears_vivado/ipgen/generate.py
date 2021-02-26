import os
import shutil
from .utils import create_folder_struct, get_folder_struct
from .ippack import ippack
from . import IPResolver
from pygears import reg
from pygears.core.gear import InSig
from pygears.hdl import hdlgen, synth
from pygears.util.fileio import save_file
from pygears.hdl.intfs.generate import generate as generate_wrap
from pygears.core.hier_node import HierVisitorBase
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


def preproc_hdl(folder, mapping=default_preproc):
    for fn in os.listdir(folder):
        fn = os.path.join(folder, fn)
        preproc_file(fn, mapping)


class IPHierVisitor(HierVisitorBase):
    def __init__(self):
        self.ips = []
        self.hdlgen_map = reg['hdlgen/map']

    def Gear(self, node):
        if node not in self.hdlgen_map:
            return

        nodeinst = self.hdlgen_map[node]
        if isinstance(nodeinst.resolver, IPResolver):
            self.ips.append(nodeinst)


def generate(top, outdir, lang, intfdef, prjdir, presynth=False):
    dirs = get_folder_struct(outdir)
    create_folder_struct(dirs)

    drv_files = []

    if presynth:
        hdl_lang = 'v'
        srcdir = os.path.join(dirs['root'], 'src')
    else:
        hdl_lang = lang
        srcdir = dirs['hdl']

    top = hdlgen(top,
                 outdir=srcdir,
                 wrapper=False,
                 copy_files=True,
                 lang=hdl_lang,
                 toplang=lang,
                 generate=True)

    topinst = reg['hdlgen/map'][top]

    if topinst.wrapped:
        try:
            shutil.copy(os.path.join(srcdir, f'{topinst.wrap_module_name}.sv'),
                        dirs['hdl'])
        except shutil.SameFileError:
            pass

    if presynth:
        if lang == 'sv':
            # TODO: Use some general file finder (as in hdl resolver)
            shutil.copy(os.path.join(srcdir, 'dti.sv'), dirs['hdl'])

        v = IPHierVisitor()
        v.visit(top)

        blackbox = [ip.node.name for ip in v.ips]

        synth('yosys',
              top=top,
              outdir=dirs['hdl'],
              lang=hdl_lang,
              synthcmd=None,
              synthout=os.path.join(dirs['hdl'], topinst.file_basename),
              blackbox=','.join(blackbox),
              srcdir=srcdir)

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

    ippack(top,
           dirs,
           intfdef=intfdef,
           lang=lang,
           prjdir=prjdir,
           files=files,
           drv_files=drv_files)

    preproc_hdl(dirs['hdl'], mapping=default_preproc)

    save_file(f'wrap_{os.path.basename(topinst.inst_name)}.{lang}',
              dirs['hdl'], wrp)
