"""Schemas of supported data types.

todo
    Use the consistent schema of JSON files for some abstract transforms...

    class JsonSchema(pa.DataFrameModel):
        id: int
        geometry: pa.Object
        tags: pa.Object

    ... and use PythonList for width_lanes (or other)

"""

import json
from pathlib import Path
from typing import Final, Literal

import geopandas as gpd
import numpy as np
import pandas as pd
import pandera as pa
import shapely
from loguru import logger
from pandera.typing.geopandas import Geometry, GeoSeries
from pyproj import CRS

DataType = Literal["building", "roadway"]


@pa.extensions.register_check_method(statistics=["geom_type", "crs"])
def check_geometry(
    geometry: GeoSeries,
    *,
    geom_type: str,
    crs: CRS = 4326,
) -> pa.typing.Series[bool]:
    """Check that geometry series has expected CRS and is of the expected geometry type.

    Parameters
    ----------
    geometry : GeoSeries
        Geometry series.
    geom_type : str
        Expected geometry type, as returned by geopandas `geom_type`.
    crs : CRS, optional
        Expected geometry CRS, by default 4326.

    Returns
    -------
    pa.typing.Series[bool]
        Returns a boolean series indicating whether or not the geometry series is in the
            expected CRS *and* whether or not each geometry matches the expected
            geometry type.

    """
    if geometry.crs != crs:
        return pd.Series(np.zeros(len(geometry)), dtype=bool)
    return geometry.geom_type.eq(geom_type)


class Building2D(pa.DataFrameModel):
    """Dataframe model for two-dimensional buildings."""

    id: int = pa.Field(gt=0)
    geometry: Geometry = pa.Field(check_geometry={"geom_type": "Polygon"})

    # TAGS

    height: float

    class Config:
        """Pandera BaseConfig."""

        add_missing_columns = True
        coerce = True
        drop_invalid_rows = True
        strict = "filter"


class Roadway2D(pa.DataFrameModel):
    """Dataframe model for two-dimensional roadways."""

    id: int = pa.Field(gt=0)
    geometry: Geometry = pa.Field(check_geometry={"geom_type": "LineString"})

    # TAGS

    highway: str  # enumeration from taginfo
    lanes: str
    width: float = pa.Field(default=np.nan)

    class Config:
        """Pandera BaseConfig."""

        add_missing_columns = True
        coerce = True
        drop_invalid_rows = True
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


DATA_TYPE_SCHEMAS: Final[dict[DataType, pa.DataFrameModel]] = {
    "building": Building2D,
    "roadway": Roadway2D,
}


def read_json(
    json_path: Path,
) -> tuple[DataType, gpd.GeoDataFrame] | tuple[Literal[None], Literal[None]]:
    """Create GeoDataFrame from JSON file with Overpass query results.

    The path stem of input file *must* be associated with a DataType.

    Parameters
    ----------
    json_path : Path
        JSON file input path, with Overpass query results.

    Returns
    -------
    tuple[DataType, gpd.GeoDataFrame] | tuple[Literal[None], Literal[None]]
        Tuple with DataType and data GeoDataFrame representation of JSON file content,
            or a tuple of (None, None) if unable to process JSON path.

    """
    try:
        with json_path.open("r") as file:
            obj = json.load(file)
    except json.JSONDecodeError as e:
        logger.error(e)
        return (None, None)
    else:
        data_type = json_path.stem
        schema = DATA_TYPE_SCHEMAS[data_type].to_schema()
        geom_type = schema.columns["geometry"].checks[0].statistics["geom_type"]
        return (
            data_type,
            schema.validate(
                make_geometry(explode_tags(pd.DataFrame(obj["elements"])), geom_type),
                lazy=True,
            ),
        )
