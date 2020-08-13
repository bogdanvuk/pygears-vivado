import os
from pygears.hdl.sv import SVModuleInst
from .ip_resolver import IPResolver


class SVVivModuleInst(SVModuleInst):
    def __init__(self, node, lang=None):
        resolver = IPResolver(node)
        super().__init__(node, resolver.lang, resolver)

    @property
    def is_generated(self):
        return True

    @property
    def include(self):
        return [os.path.join(self.ipdir, 'hdl')]

    def get_wrap_portmap(self, parent_lang):
        sig_map = {}
        for s in self.node.meta_kwds['signals']:
            sig_map[s.name] = s.name

        port_map = {}
        for p in self.node.in_ports + self.node.out_ports:
            name = p.basename
            if self.lang == 'sv':
                port_map[name] = name
            elif parent_lang == 'sv':
                sig_map[f'{name}_tvalid'] = f'{name}.valid'
                sig_map[f'{name}_tready'] = f'{name}.ready'
                sig_map[f'{name}_tdata'] = f'{name}.data'
            elif parent_lang == 'v':
                sig_map[f'{name}_tvalid'] = f'{name}_valid'
                sig_map[f'{name}_tready'] = f'{name}_ready'
                sig_map[f'{name}_tdata'] = f'{name}_data'
            else:
                port_map[name] = name

        return port_map, sig_map
