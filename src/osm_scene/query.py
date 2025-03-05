"""
Module for querying OSM data via
[Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API).

Similar functionality to
[OSMPythonTools](https://github.com/mocnik-science/osm-python-tools).

"""  # noqa: D205

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from osm_scene import Extent2D, LatLon, SimplePoly  # noqa: TC001


class QueryConfig(BaseModel):
    """Configuration for querying Overpass."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    e2: Extent2D | None = Field(
        None,
        description=(
            "Size of bounding box in x (east) and y (north) directions, respectively, "
            "in meters."
        ),
    )

    origin: LatLon | None = Field(
        None,
        description=(
            "Lower-left (southwest) corner latitude and longitude in decimal degrees."
        ),
    )

    poly: SimplePoly | None = Field(
        None,
        description=(
            "Polygon, as WKT, in EPSG:4326. "
            "If assigned, this field takes priority over querying by bbox."
        ),
    )

    @model_validator(mode="after")
    def validate_sufficient_input(self) -> Self:
        """Validate that either polygon or bbox is defined."""
        if self.poly is not None:
            return self

        if self.origin is None:
            raise ValueError("If poly not specified, origin must be.")
        if self.e2 is None:
            raise ValueError("If poly not specified, e2 must be.")
        return self
