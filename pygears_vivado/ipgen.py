import os
import glob
import tempfile
import inspect
import shutil
import jinja2

from pygears.definitions import CACHE_DIR
from pygears import registry, config
from pygears.core.gear import InSig
from pygears.util.fileio import save_if_changed, save_file
from pygears.core.hier_node import HierYielderBase
from pygears.hdl import list_hdl_files, hdlgen, find_rtl_top
from pygears.hdl.ipgen import IpgenPlugin
from pygears.hdl.templenv import TemplateEnv
from pygears.hdl.sv.generate import SVTemplateEnv
from pygears.hdl.v.generate import VTemplateEnv

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


def ippack_script(top, dirs, lang):
    base_addr = os.path.dirname(__file__)

    hdlgen_map = registry(f'{lang}gen/map')
    modinst = hdlgen_map[top]
    wrap_name = f'wrap_{modinst.module_name}'

    files = [dirs['hdl']]
    for rtl, mod in hdlgen_map.items():
        if isinstance(mod, SVVivModuleInst):
            for f in mod.files:
                os.remove(os.path.join(dirs['hdl'], os.path.basename(f)))

            xci = glob.glob(f'{mod.ipdir}/*.xci')[0]
            xci_local = os.path.join(dirs['hdl'], os.path.basename(xci))
            shutil.copyfile(xci, xci_local)
            files.append(xci_local)

    context = {
        'prjdir': '/tmp/tmp2daj9zaa',
        'hdldir': dirs['hdl'],
        'ipdir': dirs['root'],
        'ip_name': top.basename,
        'wrap_name': wrap_name,
        'files': files,
        'description': '"PyGears {} IP"'.format(modinst.module_basename)
    }

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(base_addr),
                             trim_blocks=True,
                             lstrip_blocks=True)
    env.globals.update(zip=zip)
    # env.add_extension('jinja2.ext.do')

    res = env.get_template('ippack.j2').render(context)
    save_file('ippack.tcl', dirs['script'], res)


def makefile_script(top, design, dirs, lang, hdl_include, copy):

    seen = set()
    seen_add = seen.add
    py_files = [
        x for x in py_files_enum(top) if not (x in seen or seen_add(x))
    ]

    context = {
        'py_sources': sorted(py_files),
        'ip_dir': dirs['root'],
        'ip_component_fn': os.path.join(dirs['root'], 'component.xml'),
        'hdl_include_path': [f'-I {p}' for p in hdl_include],
        'design_path': design,
        'top_path': top.name,
        'lang': lang,
        'copy': copy
    }

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(
        os.path.dirname(__file__)),
                             trim_blocks=True,
                             lstrip_blocks=True)
    env.globals.update(zip=zip)

    res = env.get_template('ipgen_makefile.j2').render(context)

    save_if_changed('Makefile', dirs['root'], res)


def get_folder_struct(outdir):
    dirs = {n: os.path.join(outdir, n) for n in ['hdl', 'script', 'doc']}
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


def py_files_enum(rtlnode):
    for node in RtlNodeYielder().visit(rtlnode):
        yield os.path.abspath(inspect.getfile(node.gear.func))

    for t in node.gear.trace:
        yield os.path.abspath(inspect.getframeinfo(t[0]).filename)


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


def ipgen(top, design, outdir, include, lang, build, copy, makefile):

    if outdir is None:
        rtl_top = find_rtl_top(top)
        outdir = os.path.join(config['vivado/iplib'], rtl_top.basename)

    dirs = get_folder_struct(outdir)
    os.makedirs(dirs['root'], exist_ok=True)

    include += config[f'{lang}gen/include']

    rtlnode = hdlgen(top,
                     outdir=dirs['hdl'],
                     wrapper=False,
                     generate=not makefile,
                     copy_files=True,
                     language=lang)

    if makefile:
        makefile_script(rtlnode,
                        design=design,
                        dirs=dirs,
                        lang=lang,
                        hdl_include=include,
                        copy=copy)
    else:
        create_folder_struct(dirs)
        ippack_script(rtlnode, dirs, lang=lang)

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

        context = {
            'wrap_module_name': f'wrap_{modinst.module_name}',
            'module_name': modinst.module_name,
            'inst_name': modinst.inst_name,
            'intfs': list(modinst.port_configs),
            'sigs': sigs,
            'param_map': modinst.params
        }

        wrp = TemplateEnv(os.path.dirname(__file__)).render_local(
            __file__, 'ip_hdl_wrap.j2', context)
        save_file(f'wrap_{os.path.basename(modinst.file_name)}', dirs['hdl'],
                  wrp)

        if build:
            run(os.path.join(dirs['script'], 'ippack.tcl'))


class VivadoIpgenPlugin(IpgenPlugin):
    @classmethod
    def bind(cls):
        config.define('vivado/iplib',
                      default=os.path.join(CACHE_DIR, 'vivado', 'iplib'))
        config['ipgen/backend']['vivado'] = ipgen
        config['ipgen/subparser'].add_parser(
            'vivado', parents=[config['ipgen/baseparser']])
