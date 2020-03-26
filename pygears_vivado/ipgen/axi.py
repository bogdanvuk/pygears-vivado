from pygears.typing import Queue, Union, typeof, Tuple
from pygears.typing.math import ceil_chunk, ceil_pow2

def get_axi_conf(top, conf):
    axi_port_cfg = {}

    for p, i in zip(top.in_ports + top.out_ports, conf):
        dtype = p.dtype
        w_data = int(dtype)
        w_eot = 0
        w_addr = 0
        if typeof(dtype, Queue):
            w_data = int(dtype.data)
            w_eot = int(dtype.eot)
            width = ceil_chunk(ceil_pow2(int(w_data)), 32)
        elif (i == 'bram' or i == 'bram.req') and typeof(dtype, Tuple):
            w_addr = dtype[0].width
            w_data = dtype[1].width

            if typeof(dtype[1], Union):
                w_data -= 1

            width = ceil_chunk(ceil_pow2(int(w_data)), 32)
        elif i == 'bram.resp':
            continue
        else:
            width = ceil_chunk(w_data, 8)

        port_cfg = {
            'width': width,
            'w_data': w_data,
            'w_eot': w_eot,
            'w_addr': w_addr,
            'name': p.basename,
            'direction': p.direction,
            'type': i
        }
        axi_port_cfg[p.basename] = port_cfg

    for p, i in zip(top.out_ports, conf[len(top.in_ports):]):
        dtype = p.dtype

        if i == 'bram.resp':
            for pi, ii in zip(top.in_ports, conf):
                if ii == 'bram.req':
                    axi_port_cfg[pi.basename]['resp'] = {
                        'w_data': dtype.width,
                        'name': p.basename,
                        'type': ii
                    }

    return axi_port_cfg
