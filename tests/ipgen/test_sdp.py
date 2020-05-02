from pygears.lib import sdp
from pygears_vivado.test_utils import ipgen_test
from pygears import Intf
from pygears.typing import Tuple, Uint


@ipgen_test(
    top='/sdp',
    intf={
        's_axi': {
            'type': 'axi',
            'araddr': 'rd_addr',
            'rdata': 'rd_data',
            'awaddr': 'wr_addr_data',
            'wdata': 'wr_addr_data'
        }
    })
def test_basic(tmpdir):
    sdp(Intf(Tuple[Uint[8], Uint[32]]), Intf(Uint[8]))
