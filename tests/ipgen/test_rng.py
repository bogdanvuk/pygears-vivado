from pygears.lib import qrange
from pygears_vivado.test_utils import ipgen_test
from pygears import Intf
from pygears.typing import Uint


@ipgen_test(top='/qrange', intf={'stop': 'axi', 'dout': 'axidma'})
def test_basic(tmpdir):
    qrange(Intf(Uint[8]))
