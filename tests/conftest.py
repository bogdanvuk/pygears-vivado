from pygears_vivado.test_utils import ipgen_test_fixture

from pygears import reg
import pytest
@pytest.fixture(autouse=True)
def load_conf(tmpdir):
    reg['results-dir'] = tmpdir
