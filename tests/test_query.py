"""Test query module."""

import pytest
import shapely
from pydantic import ValidationError

from osm_scene import query


def test_query_config_default():
    with pytest.raises(
        ValidationError,
        match="Value error, If poly not specified, origin must be.",
    ):
        _ = query.QueryConfig()


def test_query_config_no_origin():
    with pytest.raises(
        ValidationError,
        match="Value error, If poly not specified, origin must be.",
    ):
        _ = query.QueryConfig()


def test_query_config_no_s():
    with pytest.raises(
        ValidationError,
        match="Value error, If poly not specified, e2 must be.",
    ):
        _ = query.QueryConfig(origin=(0, 0))


POLY_TO_TEST = shapely.Polygon([(0, 0), (1, 0), (1, 1)])
POLY_TO_TEST_WKT = "POLYGON ((0 0, 1 0, 1 1, 0 0))"


@pytest.mark.parametrize("poly_in", [POLY_TO_TEST, POLY_TO_TEST_WKT])
def test_query_config_poly(poly_in):
    cfg = query.QueryConfig(poly=poly_in)
    assert cfg.poly == POLY_TO_TEST
    assert cfg.origin is None
    assert cfg.e2 is None


def test_query_config_poly_empty():
    with pytest.raises(
        ValidationError,
        match="Value error. Simple Polygon must not be empty.",
    ):
        _ = query.QueryConfig(poly=shapely.Polygon())


def test_query_config_poly_non_simple():
    with pytest.raises(
        ValidationError,
        match="Value error. Simple Polygon must be simple.",
    ):
        _ = query.QueryConfig(
            poly=shapely.Polygon([(0, 0), (0, 1), (1, 1), (1, 2), (0, 0)]),
        )
