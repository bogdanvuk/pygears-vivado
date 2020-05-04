import pytest
import os
import time
import serial

from pygears import find
from pygears.hdl.ipgen import ipgen
from pygears.hdl.intfs.axi import get_axi_conf

def ipgen_test(top, intf, **kwds):
    def decorator(func):
        return pytest.mark.usefixtures('ipgen_test_fixture')(
            pytest.mark.parametrize(
                'ipgen_test_fixture', [[top, intf, kwds]],
                indirect=True)(func))

    return decorator

@pytest.fixture
def ipgen_test_fixture(tmpdir, request):
    yield

    # import shutil
    # tmpdir = '/tools/home/tmp/auto_axi_test'
    # shutil.rmtree(tmpdir, ignore_errors=True)

    modname = request.module.__name__.split('.')[-1]
    testname = f'{modname}_{request.function.__name__}'
    testdir = os.path.dirname(request.module.__file__)

    top = find(request.param[0])

    inputs = []
    outputs = []
    axilite = []
    intfdef = get_axi_conf(top, request.param[1])
    for name, conf in intfdef.items():
        if conf.t == 'axi':
            if 'rdata' in conf.comp:
                inputs.extend([name, str(conf.comp['rdata'].params['rdata'])])
            elif 'wdata' in conf.comp:
                inputs.extend([name, str(conf.comp['wdata'].params['wdata'])])
        elif conf.t == 'axidma':
            if 'rdata' in conf.comp:
                outputs.extend([name, str(conf.comp['rdata'].params['rdata'])])
        elif conf.t == 'axilite':
            axilite.append(name)

    ipgen(
        'vivado',
        __file__,
        outdir=f'{tmpdir}/ip/{top.basename}',
        top=top,
        lang='sv',
        prjdir=f'{tmpdir}/ipprj',
        intf=request.param[1])

    inputs = " ".join(inputs)
    outputs = " ".join(outputs)
    axilite = " ".join(axilite)
    tcl = os.path.join(testdir, 'viv_testprj.tcl')
    os.system(f'vivado -mode batch -source {tcl} -nolog -nojournal -tclargs "{testdir}" "{tmpdir}" "{top.basename}" "{inputs}" "{outputs}" "{axilite}"')

    tcl = os.path.join(testdir, 'xsct_testprj.tcl')
    os.system(f'xsct {tcl} "{testdir}" "{tmpdir}" "{testname}"')

    def str_readout(ser, timeout=0.01):
        res = ''
        while True:
            time.sleep(0.01)
            rout = ser.read(size=1024)
            if not len(rout):
                break

            res += rout.decode()

        return res

    with serial.Serial('/dev/ttyUSB1', 115200, timeout=0.5) as ser:
        tcl = os.path.join(testdir, 'xsdb_testprj.tcl')
        os.system(f'xsdb -quiet {tcl} "{testdir}" "{tmpdir}"')
        assert str_readout(ser).strip() == 'SUCCESS'
