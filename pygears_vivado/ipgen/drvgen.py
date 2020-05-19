import os
from copy import deepcopy
import jinja2

from pygears import reg
from pygears.util.fileio import copy_file, save_file
from pygears.hdl.templenv import TemplateEnv
from pygears.typing.visitor import TypingVisitorBase
from pygears.typing import Fixp, Integral, typeof


class TypeVisitor(TypingVisitorBase):
    def __init__(self):
        self.hier = []
        self.offset = 0
        self.regs = []
        self.ctrl = []

    def func_reg(self, path, offset, width, type_):
        self.regs.append(
            {
                'path': path.copy(),
                'offset': offset,
                'width': width,
                'ctrl': deepcopy(self.ctrl),
                'type': type_
            })

    def visit_queue(self, type_, field):
        self.visit(type_[0], 'data')
        self.func_reg(self.hier + ['eot'], self.offset, int(type_[1:]), type_[1:])
        self.offset += int(type_[1:])

    def visit_union(self, type_, field):
        start_offset = self.offset
        for i, (t, f) in enumerate(zip(type_.types(), type_.fields)):
            self.offset = start_offset
            self.ctrl.append({'val': i, 'path': self.hier + ['ctrl']})
            self.visit(t, f)
            self.ctrl.pop()

        self.offset = start_offset + int(type_[0])
        self.func_reg(self.hier.copy() + ['ctrl'], self.offset, int(type_[1]), type_[1])
        self.offset += int(type_[1])

    def visit(self, type_, field=None):
        if field:
            self.hier.append(field)

        self.func_reg(self.hier, self.offset, int(type_), type_)

        if typeof(type_, Integral):
            self.offset += int(type_)
        else:
            super().visit(type_, field)

        if self.hier:
            self.hier.pop()


def type_build_module(dtype, name):
    v = TypeVisitor()
    v.visit(dtype)
    regs = v.regs
    regs = list(filter(lambda r: r['width'] > 0, regs))
    for r in regs:
        r['path'] = '_'.join(r['path'])
        if r['ctrl']:
            r['ctrl'][0]['path'] = '_'.join(r['ctrl'][0]['path'])

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        trim_blocks=True,
        lstrip_blocks=True)

    env.globals.update(repr=repr, len=len, typeof=typeof, Fixp=Fixp)

    c_content = env.get_template("drivers/type_build_c.j2").render(
        regs=regs, module_name=name, dtype=dtype)

    h_content = env.get_template("drivers/type_build_h.j2").render(
        regs=regs, module_name=name, dtype=dtype)

    return c_content, h_content


def drvgen(top, intfdef, outdir):
    xparams = []
    for name, usr_axip in intfdef.items():
        if usr_axip.t == 'axidma':
            xparams.append(f'"C_{name.upper()}_CTRL_BASEADDR"')
        elif usr_axip.t == 'axi':
            xparams.append(f'"C_{name.upper()}_BASEADDR"')

    modinst = reg('hdlgen/map')[top]
    drvname = modinst.module_name

    files_dir = os.path.join(os.path.dirname(__file__), '..', 'drivers')
    env = TemplateEnv(files_dir)

    context = {'module_name': drvname, 'params': ' '.join(xparams)}

    files = []

    outdir = os.path.join(outdir, f'{drvname}_v1_0')
    datadir = os.path.join(outdir, 'data')
    srcdir = os.path.join(outdir, 'src')

    os.makedirs(datadir, exist_ok=True)
    os.makedirs(srcdir, exist_ok=True)

    files.append(
        save_file(
            f'{drvname}.mdd', datadir,
            env.render('.', 'drvgen_mdd.j2', context)))

    files.append(
        save_file(
            f'{drvname}.tcl', datadir,
            env.render('.', 'drvgen_tcl.j2', context)))

    context = {'module_name': drvname, 'intfdef': intfdef}

    files.append(
        save_file(
            f'{drvname}.h', srcdir,
            env.render('.', 'drvgen_new_h.j2', context)))

    files.append(
        save_file(
            f'{drvname}.c', srcdir,
            env.render('.', 'drvgen_new_c.j2', context)))

    files.append(copy_file('Makefile', srcdir, os.path.join(files_dir, 'Makefile')))

    files.append(copy_file('pgaxi.c', srcdir, os.path.join(files_dir, 'pgaxi.c')))
    files.append(copy_file('pgaxi.h', srcdir, os.path.join(files_dir, 'pgaxi.h')))

    return files
