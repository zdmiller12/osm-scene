"""Test utilities."""

from osm_scene import utils


def test_utils_import():
    from types import ModuleType

    assert isinstance(utils, ModuleType)
