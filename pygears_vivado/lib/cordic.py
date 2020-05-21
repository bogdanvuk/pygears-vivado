import os
import math
from pygears import gear
from pygears.typing import Fixp, Tuple
from pygears_vivado.vivmod import SVVivModuleInst
from pygears.core.gear import InSig

# TODO: Make it work properly with widths that are not multiple of 8


@gear(hdl={'hdlgen_cls': SVVivModuleInst},
      sigmap={'aclk': 'clk'},
      signals=[InSig('aclk', 1)])
async def cordic(s_axis_phase: Fixp[3, 'W'],
                 *,
                 output_width=b'input_width',
                 input_width=b'W',
                 functional_selection="Sin_and_Cos",
                 phase_format="Scaled_Radians",
                 flow_control="Blocking",
                 out_tready=True,
                 data_format="SignedFraction",
                 _w_out=b'((W+7)//8)*8') -> {
                     'm_axis_dout': Tuple[Fixp[2, '_w_out'], Fixp[2, '_w_out']]
                 }:
    async with s_axis_phase as p:
        yield (Fixp[2, output_width](math.cos(math.pi * float(p))),
               Fixp[2, output_width](math.sin(math.pi * float(p))))
