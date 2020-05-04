from pygears.lib import accum
from pygears import gear
from pygears_vivado.test_utils import ipgen_test
from pygears import Intf
from pygears.typing import Tuple, Uint, Queue

@ipgen_test(
    top='/accum',
    intf={
        'din': {
            'type': 'axidma',
            'rdata': 'din'
        },
        'dout': {
            'type': 'axi',
            'rdata': 'dout'
        }
    })
def test_basic(tmpdir):
    @gear
    def accum_wrp(din):
        return accum(din, Uint[32](2))

    accum_wrp(Intf(Queue[Uint[32]]), name='accum')
