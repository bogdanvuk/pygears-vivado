from pygears_vivado.test_utils import ipgen_test_fixture

from pygears import config
import pytest
@pytest.fixture(autouse=True)
def load_conf(tmpdir):
    config['results-dir'] = tmpdir
