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

    def get_wrapper(self, template_env, module_name):
        port_map = {}
        for port in (self.node.in_ports + self.node.out_ports):
            name = port.basename
            port_map[f'{name}_tdata'] = f'{name}.data'
            port_map[f'{name}_tvalid'] = f'{name}.valid'
            port_map[f'{name}_tready'] = f'{name}.ready'

        context = {
            'wrap_module_name': self.module_name,
            'module_name': os.path.basename(module_name),
            'inst_name': os.path.basename(module_name),
            'intfs': list(self.port_configs),
            'sigs': self.node.params['signals'],
            'port_map': port_map,
            'sig_map': self.node.params['svgen'].get('sig_map', {}),
            'param_map': {}
        }

        return template_env.render_local(__file__, 'pygears_wrap.j2', context)

    def get_module(self, template_env):
        self.ipdir = ipinst(self.node.gear)
        return self.get_wrapper(template_env, self.ipdir)
