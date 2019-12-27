import os
import json
from copy import deepcopy
import glob
import tempfile
import inspect
import shutil
import jinja2

from pygears.definitions import CACHE_DIR
from pygears import registry, config
from pygears.core.gear import InSig
from pygears.util.fileio import save_if_changed, save_file, copy_file
from pygears.core.hier_node import HierYielderBase
from pygears.hdl import list_hdl_files, hdlgen, find_rtl
from pygears.hdl.ipgen import IpgenPlugin
from pygears.hdl.templenv import TemplateEnv
from pygears.hdl.sv.generate import SVTemplateEnv
from pygears.hdl.v.generate import VTemplateEnv
from pygears.typing.math import ceil_chunk, ceil_div, ceil_pow2
from pygears.typing.visitor import TypingVisitorBase
from pygears.typing import Uint, Int, Bool, Queue, typeof, Integral, Fixp, Tuple


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
