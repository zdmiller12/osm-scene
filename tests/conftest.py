"""Pytest configuration.

https://docs.pytest.org/en/6.2.x/customize.html

"""

from pathlib import Path

import pytest

from osm_scene import DEFAULT_DIR_IO


@pytest.fixture(scope="session")
def dir_io():
    return Path(__file__).parent.parent / DEFAULT_DIR_IO
