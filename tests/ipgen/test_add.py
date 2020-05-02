from pygears.lib import add
from pygears_vivado.test_utils import ipgen_test
from pygears import Intf
from pygears.typing import Tuple, Uint

@ipgen_test(
    top='/add',
    intf={
        'din': {
            'type': 'axi',
            'wdata': 'din'
        },
        'dout': {
            'type': 'axi',
            'rdata': 'dout'
        }
    })
def test_basic(tmpdir):
    add(Intf(Tuple[Uint[16], Uint[16]]))
