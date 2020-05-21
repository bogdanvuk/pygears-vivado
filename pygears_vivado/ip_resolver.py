import functools
import glob
import os
from pygears import reg
from pygears.hdl.base_resolver import ResolverBase, ResolverTypeError
from pygears.util.fileio import find_in_dirs
from pygears.typing import code, is_type
from pygears_vivado.ipinst import ipinst


class IPResolver(ResolverBase):
    def __init__(self, node):
        self.node = node
        self.ipdir, self._module_name = ipinst(node)

    @property
    def module_name(self):
        return self._module_name

    @property
    def lang(self):
        return os.path.splitext(self.file_basename)[-1][1:]

    @property
    def file_basename(self):
        for f in self.files:
            if os.path.basename(f).startswith(self.module_name):
                return f

    @property
    def files(self):
        files = []
        for ext in ['*.v', '*.vhd', '*.sv']:
            files.extend(glob.glob(os.path.join(self.ipdir, 'synth', ext)))

        return files

    @property
    def hdl_path_list(self):
        return reg[f'{self.lang}gen/include']

    @property
    def impl_path(self):
        return find_in_dirs(self.file_basename, self.hdl_path_list)

    @property
    def params(self):
        return {}

    def generate(self, template_env, outdir):
        pass
