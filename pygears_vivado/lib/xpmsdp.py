from pygears import gear, module, find
from pygears.lib import dreg
from pygears.typing import Tuple, Uint
from pygears.sim import clk

TWrDin = Tuple[{'addr': Uint['w_addr'], 'data': 'w_data'}]
TRdDin = Uint['w_addr']


@gear(outnames=['rd_data'],
      hdl={'hierarchical': False},
      enablement=b'latency not in [0, 2]')
async def xpmsdp(wr_addr_data: TWrDin,
                 rd_addr: TRdDin,
                 *,
                 depth=b'2**w_addr',
                 w_data=b'w_data',
                 w_addr=b'w_addr',
                 memory_primitive='auto',
                 latency=1,
                 mem=None) -> b'w_data':
    pass
