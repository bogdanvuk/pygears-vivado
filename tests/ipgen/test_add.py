from pygears.lib import add
from pygears_vivado.test_utils import ipgen_test
from pygears import Intf
from pygears.typing import Tuple, Uint


@ipgen_test(top='/add', intf={'din': 'axi', 'dout': 'axi'})
def test_basic(tmpdir):
    add(Intf(Tuple[Uint[16], Uint[16]]))


@ipgen_test(
    top='/add',
    intf={
        's_axi': {
            'type': 'axi',
            'wdata': 'din',
            'rdata': 'dout'
        }
    })
def test_combined(tmpdir):
    add(Intf(Tuple[Uint[16], Uint[16]]))
