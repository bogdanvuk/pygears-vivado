import os
import pygears_vivado
from pygears import reg
from pygears_vivado.lib.xpmsdp import xpmsdp
from pygears.sim import cosim

from pygears.lib.delay import delay_rng
from pygears.lib.verif import directed
from pygears.sim import sim
from pygears.lib.verif import drv
from pygears.typing import Tuple, Uint

def test_vivsdp_xsim_dout_throtle():
    reg['hdl/include'].append(os.path.join(os.path.dirname(pygears_vivado.lib.__file__), 'svlib'))

    reg['logger/sim/error'] = 'pass'
    wr_addr_data = [(i, i * 2) for i in range(4)]
    rd_addr = list(range(4))
    rd_data = [i * 2 for i in range(4)]

    directed(drv(t=Tuple[Uint[3], Uint[5]], seq=wr_addr_data),
             drv(t=Uint[3], seq=rd_addr) | delay_rng(1, 1),
             f=xpmsdp(memory_primitive="ultra"),
             ref=rd_data)

    cosim('/xpmsdp', 'xsim', run=True)
    sim()
