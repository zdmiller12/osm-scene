"""Common types used by OSM Scene package."""

from pathlib import Path
from typing import Annotated, Any

import numpy as np
import shapely
from pydantic import AfterValidator, BeforeValidator, Field, PlainSerializer

from osm_scene.constants import NDIGITS_DECIMAL_DEGREES, NDIGITS_METERS

type Extent2D = Annotated[
    tuple[Meters, Meters],
    PlainSerializer(
        lambda e2: np.round(e2, NDIGITS_METERS).tolist(),
        return_type=list[float],
        when_used="json",
    ),
]

type Extent3D = Annotated[
    tuple[Meters, Meters, Meters],
    PlainSerializer(
        lambda e3: np.round(e3, NDIGITS_METERS).tolist(),
        return_type=list[float],
        when_used="json",
    ),
]

type Lat = Annotated[
    float,
    Field(ge=-90, le=90),
    PlainSerializer(
        lambda lat: round(lat, NDIGITS_DECIMAL_DEGREES),
        return_type=float,
        when_used="json",
    ),
]

type Lon = Annotated[
    float,
    Field(ge=-180, le=180),
    PlainSerializer(
        lambda lon: round(lon, NDIGITS_DECIMAL_DEGREES),
        return_type=float,
        when_used="json",
    ),
]

type Meters = Annotated[
    float,
    Field(ge=0),
    PlainSerializer(
        lambda m: round(m, NDIGITS_METERS),
        return_type=float,
        when_used="json",
    ),
]

type LatLon = Annotated[
    tuple[Lat, Lon],
    PlainSerializer(
        lambda ll: np.round(ll, NDIGITS_DECIMAL_DEGREES).tolist(),
        return_type=list[float],
        when_used="json",
    ),
]


def _from_wkt(v: Any) -> shapely.Geometry:
    if isinstance(v, str):
        return shapely.from_wkt(v)
    return v


def _validate_simple_poly(v: Any) -> shapely.Polygon:
    if v.is_empty:
        error = "Simple Polygon must not be empty."
        raise ValueError(error)
    if not v.is_simple:
        error = "Simple Polygon must be simple."
        raise ValueError(error)
    return v


type SimplePoly = Annotated[
    shapely.Polygon,
    BeforeValidator(_from_wkt),
    AfterValidator(_validate_simple_poly),
    PlainSerializer(
        lambda poly: poly.wkt,
        return_type=str,
        when_used="json",
    ),
]

type PathField = Annotated[
    Path,
    AfterValidator(lambda path: path.resolve()),
    PlainSerializer(
        lambda path: str(path),
        return_type=str,
        when_used="json",
    ),
]
