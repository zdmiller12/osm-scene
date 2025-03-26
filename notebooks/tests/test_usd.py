"""Test usd notebook."""

import pytest
from testbook import testbook

EXPECTED_USD_FILES = {
    "usd/cone.usda",
    "usd/extruded-plane.usda",
    "usd/mesh.usda",
    "usd/pixar-sphere.usda",
    "usd/plane.usda",
    "usd/sandbox.usda",
    "usd/sphere.usda",
}


@pytest.fixture
def expected_usd(dir_notebooks):
    return {dir_notebooks / usd for usd in EXPECTED_USD_FILES}


@pytest.fixture
def cleanup_usd(expected_usd):  # pragma: no cover
    for usd in expected_usd:
        usd.unlink(missing_ok=True)


@pytest.mark.usefixtures("cleanup_usd")
@testbook("usd.ipynb", execute=True)
def test_usd_notebook(_, expected_usd):  # noqa: PT019
    for usd in expected_usd:
        assert usd.is_file()
