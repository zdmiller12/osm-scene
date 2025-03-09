"""Test query module."""

import json
import shutil
from unittest import mock

import pytest
import requests
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

    q = query.Query(e2=e2, origin=origin)
    assert q.poly is None
    assert q.bbox == BBox(
        west=west_deg,
        south=south_deg,
        east=expected_east_deg,
        north=expected_north_deg,
    )
    assert q.area_filter == expected_area_filter


def test_query_get_queries(tmp_path):
    dir_out = tmp_path
    poly = shapely.Polygon([(0, 0), (1, 0), (1, 1)])
    timeout_s = 180

    area_filter = '(poly:"0.0 0.0 0.0 1.0 1.0 1.0 0.0 0.0")'

    # NOTE that spacing matters
    building_query = f"""
            [out:json][timeout:{timeout_s}];
            way["building"]{area_filter};
            out tags geom;
        """
    roadway_query = f"""
            [out:json][timeout:{timeout_s}];
            (
                // "major"
                way[highway~"^(motorway|trunk|primary|secondary|tertiary|(motorway|trunk|primary|secondary)_link)$"]{area_filter};

                // "minor"
                way[highway~"^(unclassified|residential|living_street|service|pedestrian|track)$"]{area_filter};
            );
            out tags geom;
        """
    expected_queries = {
        dir_out / "building.json": building_query,
        dir_out / "roadway.json": roadway_query,
    }

    q = query.Query(
        dir_out=dir_out,
        poly=poly,
        timeout_s=timeout_s,
    )
    queries = q.get_queries()
    assert queries == expected_queries


def test_query_cli_cmd(monkeypatch, tmp_path):
    mock_json_content = {"data": "from-overpass"}
    mock_requests_get = mock.MagicMock()
    mock_requests_get.return_value.json.return_value = mock_json_content

    dir_out = tmp_path / "io"

    with monkeypatch.context() as m:
        m.setattr(requests, "get", mock_requests_get)

        q = query.Query(dir_out=dir_out, poly=shapely.Polygon([(0, 0), (1, 0), (1, 1)]))
        q.cli_cmd()

    output_paths = set(dir_out.glob("*.json"))
    assert output_paths == {dir_out / "building.json", dir_out / "roadway.json"}
    for output_path in output_paths:
        assert json.loads(output_path.read_text())

    assert set(q.response().output["output_paths"]) == output_paths
    shutil.rmtree(dir_out)


class MockRequestsResponse:
    """Class for mocking a requests.Response which will raise_for_status."""

    def raise_for_status(self):
        error = "Don't do that."
        raise requests.HTTPError(error)


def test_query_cli_cmd_error(monkeypatch, tmp_path):
    with monkeypatch.context() as m:
        m.setattr(
            query,
            "query_overpass",
            lambda *args, **kwargs: MockRequestsResponse(),  # noqa: ARG005
        )

        q = query.Query(
            dir_out=tmp_path,
            poly=shapely.Polygon([(0, 0), (1, 0), (1, 1)]),
        )
        q.cli_cmd()

    assert q.response().output["output_paths"] == []


def test_query_overpass_regex_error(monkeypatch):
    query_string = "query"

    mock_request = mock.MagicMock()
    with monkeypatch.context() as m:
        m.setattr(requests, "get", mock_request)

        _ = query.query_overpass(query_string)

    mock_request.assert_called_once_with(
        query.OVERPASS_ENDPOINT,
        timeout=query.DEFAULT_TIMEOUT_S + 1,
        params={"data": query_string},
    )
