import os


def run(tcl):
    viv_cmd = (f'vivado -mode batch -source {tcl} -nolog -nojournal')
    return os.system(viv_cmd)
