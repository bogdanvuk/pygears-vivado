import os
from pygears import gear
from pygears.hdl import hdlgen
from pygears.typing import Uint
from pygears.typing.math import ceil_chunk
from pygears.core.gear import InSig
from pygears import Intf
from pygears_vivado.ipinst import ipinst
from pygears_vivado.vivmod import SVVivModuleInst

@gear(
    hdl={'hdlgen_cls': SVVivModuleInst},
    sigmap={
        's_axis_aresetn': '~rst',
        's_axis_aclk': 'clk'
    },
    signals=[InSig('s_axis_aresetn', 1),
             InSig('s_axis_aclk', 1)],
)
async def axis_data_fifo(
        s_axis: Uint['W'],
        *,
        tdata_num_bytes=b'W//8',
        fifo_depth=b'depth'
) -> {
        'm_axis': b's_axis'
}:
    pass


@gear
def viv_fifo(din, *, depth):
    return axis_data_fifo(din >> Uint[ceil_chunk(din.dtype.width, 8)], fifo_depth=depth) >> din.dtype


# from pygears.lib import decouple


# @gear
# def top(din):
#     return din \
#         | decouple \
#         | viv_fifo(depth=8192) \
#         | decouple


# top(Intf(Uint[1024]))

# # hdlgen(top='/top', lang='sv', outdir='/work/gears-knn/gears_knn/build/synth_test/viv_fifo', copy_files=True)

# from pygears.hdl import synth
# synth(
#     'vivado',
#     outdir='/work/gears-knn/gears_knn/build/synth_test/viv_fifo_2',
#     prjdir='/work/gears-knn/gears_knn/build/synth_prj/viv_fifo_2',
#     top='/top',
#     lang='sv',
#     util=True,
#     part="xcvu9p-flgb2104-2-i")

# # from pygears.sim import sim, cosim
# # from pygears.lib import drv, collect
# # # Intf(Uint[8]) | axis_data_fifo
# # res = []
# # drv(t=Uint[8], seq=[1, 2, 3]) | axis_data_fifo | collect(result=res)

# # cosim('/axis_data_fifo', 'xsim', run=False)
# # sim('/tools/home/tmp')
# # print(res)
