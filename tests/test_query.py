"""Test query module."""

import pytest
import shapely
from pydantic import ValidationError
from pyproj.aoi import BBox

from osm_scene import query


def test_query_config_default():
    with pytest.raises(
        ValidationError,
        match="Value error, If poly not specified, origin must be.",
    ):
        query.Query()


def test_query_config_no_origin():
    with pytest.raises(
        ValidationError,
        match="Value error, If poly not specified, origin must be.",
    ):
        query.Query()


def test_query_config_no_e2():
    with pytest.raises(
        ValidationError,
        match="Value error, If poly not specified, e2 must be.",
    ):
        query.Query(origin=(0, 0))


POLY_TO_TEST = shapely.Polygon([(0, 0), (1, 0), (1, 1)])
POLY_TO_TEST_WKT = "POLYGON ((0 0, 1 0, 1 1, 0 0))"


@pytest.mark.parametrize("poly_in", [POLY_TO_TEST, POLY_TO_TEST_WKT])
def test_query_config_poly(poly_in):
    cfg = query.Query(poly=poly_in)
    assert cfg.poly == POLY_TO_TEST
    assert cfg.origin is None
    assert cfg.e2 is None
    assert cfg.area_filter == '(poly:"0.0 0.0 0.0 1.0 1.0 1.0 0.0 0.0")'
    with pytest.raises(ReferenceError, match="Cannot get bbox from poly"):
        _ = cfg.bbox


def test_query_config_poly_empty():
    with pytest.raises(
        ValidationError,
        match="Value error. Simple Polygon must not be empty.",
    ):
        query.Query(poly=shapely.Polygon())


def test_query_config_poly_non_simple():
    non_simple_polygon = shapely.Polygon([(0, 0), (0, 1), (1, 1), (1, 2), (0, 0)])

    with pytest.raises(
        ValidationError,
        match="Value error. Simple Polygon must be simple.",
    ):
        query.Query(poly=non_simple_polygon)


def test_query_config_bbox():
    south_deg = 0
    west_deg = 0

    e2 = (50, 100)
    origin = (south_deg, west_deg)

    expected_east_deg = 0.0008983152841195215
    expected_north_deg = 0.00045218473852509677

    expected_area_filter = "(0.000000, 0.000000, 0.000452, 0.000898)"

    cfg = query.Query(e2=e2, origin=origin)
    assert cfg.poly is None
    assert cfg.bbox == BBox(
        west=west_deg,
        south=south_deg,
        east=expected_east_deg,
        north=expected_north_deg,
    )
    assert cfg.area_filter == expected_area_filter
