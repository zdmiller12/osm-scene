"""Schemas of supported data types.

todo
    Use the consistent schema of JSON files for some abstract transforms...

    class JsonSchema(pa.DataFrameModel):
        id: int
        geometry: pa.Object
        tags: pa.Object

    ... and use PythonList for width_lanes (or other)

"""

import abc
import copy
import json
from pathlib import Path
from typing import Annotated, Any, Generic, Literal, Self, TypeVar, final

import geopandas as gpd
import numpy as np
import pandas as pd
import pandera as pa
import shapely
from loguru import logger
from pandera.typing.geopandas import GeoDataFrame, Geometry, GeoSeries
from pydantic import BaseModel, Field, RootModel, model_validator
from pyproj import CRS

import osm_scene._types as t


@pa.extensions.register_check_method(statistics=["geom_type", "crs"])
def check_geometry(
    geometry: GeoSeries,
    *,
    geom_type: str,
    crs: CRS,
) -> pa.typing.Series[bool]:
    """Check that geometry series has expected CRS and is of the expected geometry type.

    Parameters
    ----------
    geometry : GeoSeries
        Geometry series.
    geom_type : str
        Expected geometry type, as returned by geopandas `geom_type`.
    crs : CRS, optional
        Expected geometry CRS.

    Returns
    -------
    pa.typing.Series[bool]
        Returns a boolean series indicating whether or not the geometry series is in the
            expected CRS *and* whether or not each geometry matches the expected
            geometry type.

    """
    if geometry.empty:
        return True
    if geometry.crs != crs:
        return pd.Series(np.zeros(len(geometry)), dtype=bool)
    return geometry.geom_type.eq(geom_type)


class JsonModel(pa.DataFrameModel):
    """Dataframe model for Overpass results as JSON."""

    id: int
    geometry: pa.Object
    tags: pa.Object


class Building2D(pa.DataFrameModel):
    """Dataframe model for two-dimensional buildings."""

    id: int = pa.Field(default=0, gt=0)
    geometry: Geometry = pa.Field(
        check_geometry={"geom_type": "Polygon", "crs": 4326},
        default=shapely.Polygon(),
    )

    # TAGS

    height: float = pa.Field(gt=0, nullable=True)

    class Config:
        """Pandera BaseConfig."""

        add_missing_columns = True
        coerce = True
        strict = "filter"


class Building3D(pa.DataFrameModel):
    """Dataframe model for three-dimensional buildings."""

    id: int = pa.Field(default=0, gt=0)
    geometry: Geometry = pa.Field(
        check_geometry={"geom_type": "Polygon", "crs": 4326},
        default=shapely.Polygon(),
    )

    class Config:
        """Pandera BaseConfig."""

        add_missing_columns = True
        coerce = True
        strict = "filter"


class Roadway2D(pa.DataFrameModel):
    """Dataframe model for two-dimensional roadways."""

    id: int = pa.Field(default=0, gt=0)
    geometry: Geometry = pa.Field(
        check_geometry={"geom_type": "LineString", "crs": 4326},
        default=shapely.LineString(),
    )

    # TAGS

    highway: str = pa.Field(default="", str_length={"min_value": 1})
    lanes: int = pa.Field(default=2, gt=0)
    width: float = pa.Field(nullable=True)

    class Config:
        """Pandera BaseConfig."""

        add_missing_columns = True
        coerce = True
        strict = "filter"


class Roadway3D(pa.DataFrameModel):
    """Dataframe model for three-dimensional roadways."""

    id: int = pa.Field(default=0, gt=0)
    geometry: Geometry = pa.Field(
        check_geometry={"geom_type": "LineString", "crs": 4326},
        default=shapely.LineString(),
    )

    class Config:
        """Pandera BaseConfig."""

        add_missing_columns = True
        coerce = True
        strict = "filter"


def explode_tags(df: pd.DataFrame) -> pd.DataFrame:
    """Explode 'tags' column of dictionaries into new columns.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with tags column to explode.

    Returns
    -------
    pd.DataFrame
        DataFrame with exploded tags column, or a copy of the input DataFrame if it does
            not have a tags column.

    """
    if "tags" not in df.columns:
        return df.copy()

    return df.drop(columns=["tags"]).merge(
        pd.json_normalize(df["tags"].to_list()).set_index(df.index),
        left_index=True,
        right_index=True,
        suffixes=(None, "_tag"),
    )


def get_geom_type(model: pa.DataFrameModel) -> str:
    """Get geometry type from pandera DataFrameModel.

    The model *must* have a 'geometry' column, for which there is a 'check_geometry'
    check enforced.

    Parameters
    ----------
    model : pa.DataFrameModel
        pandera DataFrameModel.

    Returns
    -------
    str
        shapely geometry type.

    """
    return model.to_schema().columns["geometry"].checks[0].statistics["geom_type"]


def make_geometry(
    df: pd.DataFrame,
    geom_type: Literal["LineString", "Polygon"],
) -> gpd.GeoDataFrame:
    """Create proper GeoSeries geometry column from list of lat lon dictionaries.

    Geometries are cast into `geom_type` geometry types.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with geometry column as list of lat lon dictionaries.
    geom_type : Literal[&quot;LineString&quot;, &quot;Polygon&quot;]
        Geometry type.

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame with proper GeoSeries geometry column, in EPSG:4326, or a copy of
            the input DataFrame if it does not have a geometry column.

    """
    if "geometry" not in df.columns:
        return df.copy()

    return gpd.GeoDataFrame(
        df.drop(columns=["geometry"]),
        crs=4326,
        geometry=df["geometry"]
        .map(lambda ll_list: [[ll["lon"], ll["lat"]] for ll in ll_list])
        .map(getattr(shapely, geom_type)),
    )


DataType = Literal["building", "roadway"]

Model2D = TypeVar("Model2D", bound=pa.DataFrameModel)
Model3D = TypeVar("Model3D", bound=pa.DataFrameModel)


class FeatureSetBase(BaseModel, abc.ABC, Generic[Model2D, Model3D]):
    """Abstract pydantic BaseModel for datasets, like buildings, roadways, etc."""

    data_type: DataType

    gdf_2d: GeoDataFrame[Model2D]
    gdf_3d: GeoDataFrame[Model3D]

    json_path: t.PathField

    @classmethod
    def columns_2d(cls) -> list[str]:
        """Columns of two-dimensional geodataframe."""
        return list(cls.schema_2d().columns.keys())

    @classmethod
    def columns_3d(cls) -> list[str]:
        """Columns of three-dimensional geodataframe."""
        return list(cls.schema_3d().columns.keys())

    @classmethod
    def geom_type_2d(cls) -> str:
        """Shapely geometry type of three-dimensional feature set."""
        return get_geom_type(cls.model_2d())

    @classmethod
    def geom_type_3d(cls) -> str:
        """Shapely geometry type of three-dimensional feature set."""
        return get_geom_type(cls.model_3d())

    @classmethod
    def model_2d(cls) -> pa.DataFrameModel:
        """Pandera DataFrameModel for two-dimensional feature set."""
        return cls.mro()[1].__pydantic_generic_metadata__["args"][0]

    @classmethod
    def model_3d(cls) -> pa.DataFrameModel:
        """Pandera DataFrameModel for three-dimensional feature set."""
        return cls.mro()[1].__pydantic_generic_metadata__["args"][1]

    @classmethod
    def schema_2d(cls) -> pa.DataFrameSchema:
        """Pandera DataFrameSchema for two-dimensional feature set."""
        return cls.model_2d().to_schema()

    @classmethod
    def schema_2d_lazy(cls) -> pa.DataFrameSchema:
        """Two-dimensional DataFrameSchema to use for lazy validation."""
        schema = copy.deepcopy(cls.schema_2d())
        schema.drop_invalid_rows = True
        return schema

    @classmethod
    def schema_3d(cls) -> pa.DataFrameSchema:
        """Pandera DataFrameSchema for three-dimensional feature set."""
        return cls.model_3d().to_schema()

    @classmethod
    def schema_3d_lazy(cls) -> pa.DataFrameSchema:
        """Three-dimensional DataFrameSchema to use for lazy validation."""
        schema = copy.deepcopy(cls.schema_3d())
        schema.drop_invalid_rows = True
        return schema

    @model_validator(mode="before")
    @classmethod
    def build_gdfs(cls, data: Any) -> Any:  # noqa: ANN401
        """Finish populating feature set model by building geodataframes."""
        try:
            with data["json_path"].open("r") as file:
                obj = json.load(file)
        except json.JSONDecodeError as e:
            logger.error(e)
            data["gdf_2d"] = gpd.GeoDataFrame(columns=cls.columns_2d())
            data["gdf_3d"] = gpd.GeoDataFrame(columns=cls.columns_3d())
        else:
            data["gdf_2d"] = cls.schema_2d_lazy().validate(
                make_geometry(
                    explode_tags(pd.DataFrame(obj["elements"])),
                    cls.geom_type_2d(),
                ),
                lazy=True,
            )
            data["gdf_3d"] = cls.to_3d(data["gdf_2d"])
        return data

    @classmethod
    @abc.abstractmethod
    @pa.check_types
    def to_3d(cls, gdf: GeoDataFrame[Model2D]) -> GeoDataFrame[Model3D]:
        """Convert two-dimensional data to three-dimensional."""


@final
class Building(FeatureSetBase[Building2D, Building3D]):
    """Building feature set."""

    data_type: Literal["building"] = "building"

    @classmethod
    def to_3d(cls, gdf: GeoDataFrame[Building2D]) -> GeoDataFrame[Building3D]:
        """Convert 2D buildings to 3D."""
        return gdf


@final
class Roadway(FeatureSetBase[Roadway2D, Roadway3D]):
    """Roadway feature set."""

    data_type: Literal["roadway"] = "roadway"

    @classmethod
    def to_3d(cls, gdf: GeoDataFrame[Roadway2D]) -> GeoDataFrame[Roadway3D]:
        """Convert 2D roadways to 3D."""
        return gdf


FeaturesType = Annotated[
    Building | Roadway,
    Field(discriminator="data_type"),
]


class FeatureSet(RootModel):
    """Pydantic root model for a feature set."""

    root: FeaturesType

    @classmethod
    def from_json_path(cls, json_path: Path) -> Self:
        """Build feature set from JSON path with Overpass results."""
        return cls(data_type=json_path.stem, json_path=json_path)


class Features(RootModel):
    """Pydantic root model for the collection of all feature sets."""

    root: list[FeaturesType]
