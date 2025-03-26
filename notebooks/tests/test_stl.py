"""Test stl notebook."""

import pytest
from testbook import testbook

EXPECTED_STL_FILES = {
    "stl/Cube.figure.pickle",
}


@pytest.fixture
def expected_stl(dir_notebooks):
    return {dir_notebooks / stl for stl in EXPECTED_STL_FILES}


@pytest.fixture
def cleanup_stl(expected_stl):  # pragma: no cover
    for stl in expected_stl:
        stl.unlink()


@pytest.mark.usefixtures("cleanup_stl")
@testbook("stl.ipynb", execute=True)
def test_usd_notebook(_, expected_stl):  # noqa: PT019
    for stl in expected_stl:
        assert stl.exists()
