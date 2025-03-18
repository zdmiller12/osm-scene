"""Test schemas module."""

import copy
import re

import geopandas as gpd
import pandas as pd
import pandera as pa
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
    invalid_building = valid_building.to_crs(3857)

    building_schema = copy.deepcopy(schemas.Building2D.to_schema())

    # strict
    with pytest.raises(
        pa.errors.SchemaError,
        match=re.escape(
            "Column 'geometry' failed element-wise validator number 0: "
            "check_geometry(geom_type=Polygon, crs=4326)",
        ),
    ):
        building_schema.validate(invalid_building)

    # lazy
    building_schema.drop_invalid_rows = True
    gdf_validated = building_schema.validate(invalid_building, lazy=True)
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


def test_feature_set(tmp_path):
    dir_in = tmp_path / "io"
    dir_in.mkdir()

    path_building = dir_in / "building.json"
    path_roadway = dir_in / "roadway.json"

    path_building.touch()
    path_roadway.touch()

    buildings = schemas.FeatureSet.from_json_path(path_building).root
    assert buildings.geom_type_2d() == "Polygon"
    assert buildings.geom_type_3d() == "Polygon Z"
    assert buildings.model_2d() == schemas.Building2D
    assert buildings.model_3d() == schemas.Building3D
    assert buildings.schema_2d() == schemas.Building2D.to_schema()
    assert buildings.schema_3d() == schemas.Building3D.to_schema()
    assert buildings.schema_2d_lazy().drop_invalid_rows
    assert buildings.schema_3d_lazy().drop_invalid_rows

    roadways = schemas.FeatureSet.from_json_path(path_roadway).root
    assert roadways.geom_type_2d() == "LineString"
    assert roadways.geom_type_3d() == "LineString Z"
    assert roadways.model_2d() == schemas.Roadway2D
    assert roadways.model_3d() == schemas.Roadway3D
    assert roadways.schema_2d() == schemas.Roadway2D.to_schema()
    assert roadways.schema_3d() == schemas.Roadway3D.to_schema()
    assert roadways.schema_2d_lazy().drop_invalid_rows
    assert roadways.schema_3d_lazy().drop_invalid_rows
