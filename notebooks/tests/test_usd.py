"""Test usd notebook."""

import pytest
from testbook import testbook


@pytest.fixture
def cleanup_usd_files(dir_notebooks):  # pragma: no cover
    for usd_path in dir_notebooks.glob("*.usd*"):
        usd_path.unlink()


EXPECTED_USD_PATHS = {
    "cone.usda",
    "extruded-plane.usda",
    "mesh.usda",
    "pixar-sphere.usda",
    "plane.usda",
    "sphere.usda",
}


@pytest.mark.usefixtures("cleanup_usd_files")
@testbook("usd.ipynb", execute=True)
def test_usd_notebook(_, dir_notebooks):  # noqa: PT019
    usd_paths = set()
    for usd_path in dir_notebooks.glob("*.usd*"):
        usd_paths.add(usd_path.name)
        usd_path.unlink()

    assert usd_paths == EXPECTED_USD_PATHS
