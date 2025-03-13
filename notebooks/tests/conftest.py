"""Pytest configuration for notebook tests.

https://docs.pytest.org/en/stable/reference/customize.html

"""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def dir_notebooks():
    return Path(__file__).parent.parent
