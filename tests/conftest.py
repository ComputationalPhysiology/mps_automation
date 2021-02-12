import shutil

import pytest

from tests.generate_dummy_data import main


@pytest.fixture
def test_folder():
    data_dir = main()
    yield data_dir
    shutil.rmtree(data_dir)
