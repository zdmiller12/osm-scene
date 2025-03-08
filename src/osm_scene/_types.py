"""Common types used by OSM Scene package."""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Annotated, Any

import numpy as np
import pydantic
import shapely
from annotated_types import Ge, Le

from osm_scene.constants import NDIGITS_DECIMAL_DEGREES, NDIGITS_METERS

type Extent2D = Annotated[
    tuple[Meters, Meters],
    pydantic.PlainSerializer(
        lambda e2: np.round(e2, NDIGITS_METERS).tolist(),
        return_type=list[float],
        when_used="json",
    ),
]

type Extent3D = Annotated[
    tuple[Meters, Meters, Meters],
    pydantic.PlainSerializer(
        lambda e3: np.round(e3, NDIGITS_METERS).tolist(),
        return_type=list[float],
        when_used="json",
    ),
]

type Lat = Annotated[
    float,
    Ge(-90),
    Le(90),
    pydantic.PlainSerializer(
        lambda lat: round(lat, NDIGITS_DECIMAL_DEGREES),
        return_type=float,
        when_used="json",
    ),
]

type Lon = Annotated[
    float,
    Ge(-180),
    Le(180),
    pydantic.PlainSerializer(
        lambda lon: round(lon, NDIGITS_DECIMAL_DEGREES),
        return_type=float,
        when_used="json",
    ),
]

type Meters = Annotated[
    float,
    Ge(0),
    pydantic.PlainSerializer(
        lambda m: round(m, NDIGITS_METERS),
        return_type=float,
        when_used="json",
    ),
]

type LatLon = Annotated[
    tuple[Lat, Lon],
    pydantic.PlainSerializer(
        lambda ll: np.round(ll, NDIGITS_DECIMAL_DEGREES).tolist(),
        return_type=list[float],
        when_used="json",
    ),
]


def _from_wkt(v: Any) -> shapely.Geometry:
    """Load WKT string, if needed, or just return input."""
    if isinstance(v, str):
        return shapely.from_wkt(v)
    return v


def _validate_simple_poly(v: Any) -> shapely.Polygon:
    """Validate that input is a non-empty, simple Polygon."""
    if v.is_empty:
        error = "Simple Polygon must not be empty."
        raise ValueError(error)
    if not v.is_simple:
        error = "Simple Polygon must be simple."
        raise ValueError(error)
    return v


type SimplePoly = Annotated[
    shapely.Polygon,
    pydantic.BeforeValidator(_from_wkt),
    pydantic.AfterValidator(_validate_simple_poly),
    pydantic.PlainSerializer(
        lambda poly: poly.wkt,
        return_type=str,
        when_used="json",
    ),
]

type PathField = Annotated[
    Path,
    pydantic.AfterValidator(lambda path: path.resolve()),
    pydantic.PlainSerializer(
        lambda path: str(path),
        return_type=str,
        when_used="json",
    ),
]


class Response(pydantic.BaseModel):
    """Common response model."""

    code: int = 0
    message: str = ""
    output: dict[str, Any] = pydantic.Field(default_factory=dict)


class WithResponse(pydantic.BaseModel, abc.ABC):
    """Abstract base model for consistent responses."""

    model_config = pydantic.ConfigDict(frozen=True)

    _response: Response = pydantic.PrivateAttr(default_factory=Response)

    def response(self) -> Response:
        """Get response."""
        return self._response
