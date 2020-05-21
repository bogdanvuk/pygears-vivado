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
        return self.files[0]

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
    @functools.lru_cache()
    def impl_parse(self):
        if self.impl_path:
            with open(self.impl_path, 'r') as f:
                return parse(f.read())

        return None

    @property
    def impl_params(self):
        return self.impl_parse[-1]

    @property
    def impl_intfs(self):
        parse_res = self.impl_parse()
        if parse_res:
            intfs = {}
            for i in parse_res[2]:
                intfs[i['name']] = i

            return intfs

        return None

    @property
    def params(self):
        return {}

    def generate(self, template_env, outdir):
        pass
