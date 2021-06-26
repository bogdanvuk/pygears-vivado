from pygears.lib.delay import delay_rng
from pygears_vivado.lib.axis_data_fifo import viv_fifo
from pygears.sim import cosim, sim
from pygears.typing import Uint
from pygears.lib.verif import directed, drv, verif

def test_cosim():
    seq = list(range(1, 10))
    directed(drv(t=Uint[16], seq=seq) | delay_rng(0, 2),
             f=viv_fifo(depth=16),
             ref=seq,
             delays=[delay_rng(0, 2)])

    cosim('/viv_fifo', 'xsim')
    sim()

test_cosim()
