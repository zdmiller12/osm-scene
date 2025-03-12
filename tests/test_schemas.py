"""Test schemas module."""

import geopandas as gpd
import pandas as pd
import pytest
import shapely
from geopandas.testing import assert_geodataframe_equal

from osm_scene import schemas


@pytest.fixture
def valid_building():
    building = schemas.Building2D.validate(
        gpd.GeoDataFrame(
            {"id": [2], "height": [10]},
            crs=4326,
            geometry=[shapely.Polygon([(0, 0), (1, 0), (1, 1)])],
        ),
        lazy=True,
    )
    assert not building.empty
    return building


def test_check_geometry_crs_mismatch(valid_building):
    gdf_validated = schemas.Building2D.validate(valid_building.to_crs(3857), lazy=True)
    assert gdf_validated.empty


def test_explode_tags_no_tags_column():
    df_no_tags = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df_exploded = schemas.explode_tags(df_no_tags)
    pd.testing.assert_frame_equal(df_no_tags, df_exploded)
    assert id(df_no_tags) != id(df_exploded)


def test_explode_tags():
    df_tags = pd.DataFrame(
        {
            "tags": [
                {"a": "a", "b": 1},
                {"b": 2, "c": 3.0},
            ],
        },
    )
    df_exploded = schemas.explode_tags(df_tags)
    pd.testing.assert_frame_equal(
        df_exploded,
        pd.DataFrame(
            {
                "a": ["a", None],
                "b": [1, 2],
                "c": [None, 3.0],
            },
        ),
    )


def test_make_geometry_no_geometry_column():
    df_no_geometry = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df_geometry = schemas.make_geometry(df_no_geometry, "Polygon")
    pd.testing.assert_frame_equal(df_no_geometry, df_geometry)
    assert id(df_no_geometry) != id(df_geometry)


def test_make_geometry():
    df_geometry = pd.DataFrame(
        {
            "col": ["A", "B"],
            "geometry": [
                [{"lat": 0, "lon": 1}, {"lat": 1, "lon": 2}],
                [{"lat": 2, "lon": 3}, {"lat": 3, "lon": 4}],
            ],
        },
    )
    gdf = schemas.make_geometry(df_geometry, "LineString")
    assert_geodataframe_equal(
        gdf,
        gpd.GeoDataFrame(
            {"col": ["A", "B"]},
            crs=4326,
            geometry=[
                shapely.LineString([(1, 0), (2, 1)]),
                shapely.LineString([(3, 2), (4, 3)]),
            ],
        ),
    )


def test_read_json_exception(tmp_path):
    json_path = tmp_path / "not-really-a.json"
    json_path.write_text("Howdy, doody.")

    result = schemas.read_json(json_path)
    assert result == (None, None)
