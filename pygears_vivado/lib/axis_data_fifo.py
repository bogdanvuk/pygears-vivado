import os
from pygears import gear
from pygears.typing import Uint
from pygears.core.gear import HookableDict
from pygears import Intf, config
from pygears_vivado.ipinst import ipinst
from pygears_vivado.vivmod import SVVivModuleInst

config['trace/level'] = 0

# @property
# def files(gear):
#     breakpoint()
#     return []

# @property
# def hdl_fn(gear):
#     ipdir = ipinst(gear)
#     breakpoint()
#     return []


# @gear(hdl={hdl_fn=HdlFn(), files=Files()})
# @gear(hdl={'hdl_fn': hdl_fn, 'files': files})
@gear(
    svgen={
        'svgen_cls': SVVivModuleInst,
        'sig_map': {
            's_axis_aresetn': '~rst',
            's_axis_aclk': 'clk'
        }
    })
async def axis_data_fifo(s_axis: Uint) -> {'m_axis': b's_axis'}:
    pass


from pygears.sim import sim, cosim
from pygears.lib import drv, collect
# Intf(Uint[8]) | axis_data_fifo
res = []
drv(t=Uint[8], seq=[1, 2, 3]) | axis_data_fifo | collect(result=res)

cosim('/axis_data_fifo', 'xsim', run=False)
sim('/tools/home/tmp')
print(res)
