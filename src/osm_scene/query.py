"""
Module for querying OSM data via
[Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API).

Similar functionality to
[OSMPythonTools](https://github.com/mocnik-science/osm-python-tools).

References
----------
    https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide

    https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL

"""  # noqa: D205

from __future__ import annotations

from functools import cached_property
from typing import Self

import requests
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pyproj.aoi import BBox

from osm_scene import Extent2D, LatLon, PathField, SimplePoly  # noqa: TC001
from osm_scene.constants import GEOD_WGS84, OVERPASS_ENDPOINT


class QueryConfig(BaseModel):
    """Query public Overpass API for data."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    dir_out: PathField = "io"

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

    timeout_s: int = Field(
        180,
        description="Timeout, in seconds, for Overpass queries.",
    )

    @model_validator(mode="after")
    def validate_sufficient_input(self) -> Self:
        """Validate that either polygon or bbox is defined."""
        if self.poly is not None:
            return self

        if self.origin is None:
            error = "If poly not specified, origin must be."
            raise ValueError(error)
        if self.e2 is None:
            error = "If poly not specified, e2 must be."
            raise ValueError(error)
        return self

    @cached_property
    def area_filter(self) -> str:
        """Get string for filtering elements by area.

        References
        ----------
            https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL#Bounding_box

            https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL#By_polygon_(poly)

        Returns
        -------
            String for filtering elements by area.

        """
        if self.poly is not None:
            coords = " ".join(
                f"{lat} {lon}" for lat, lon in map(reversed, self.poly.exterior.coords)
            )
            return f'(poly:"{coords}")'

        bbox = self.bbox
        return f"({bbox.south:.6f}, {bbox.west:.6f}, {bbox.north:.6f}, {bbox.east:.6f})"

    @cached_property
    def bbox(self) -> BBox:
        """Get pyproj BBox for query. Not available when defining poly.

        Use pyproj to apply two forward transformations to the origin. First north, then
        east, using distances defined by current extents.

        Returns
        -------
        BBox
            pyproj [BBox](https://pyproj4.github.io/pyproj/stable/api/aoi.html) for
                query.

        Raises
        ------
        ReferenceError
            If poly is defined.

        """
        if self.poly is not None:
            error = "Cannot get bbox from poly"
            raise ReferenceError(error)

        lons, lats, _ = GEOD_WGS84.fwd(
            lons=2 * [self.origin[1]],
            lats=2 * [self.origin[0]],
            az=[0, 90],
            dist=self.e2,
            return_back_azimuth=False,
        )
        return BBox(
            west=self.origin[1],
            south=self.origin[0],
            east=lons[1],
            north=lats[0],
        )

    def get_building_query(self) -> str:
        """Get Overpass query string for buildings."""
        return f"""
            [out:json][timeout:{self.timeout_s}];
            way["building"]{self.area_filter};
            out tags geom;
        """

    def cli_cmd(self) -> None:
        """CLI subcommand entrypoint."""
        logger.info(f"Querying with config...\n\n{self.model_dump_json(indent=4)}")


def query_overpass(query: str, query_config: QueryConfig) -> requests.Response:
    """Query Overpass.

    Parameters
    ----------
    query : str
        Query string.
    query_config : QueryConfig
        Query configuration.

    Returns
    -------
    requests.Response
        Overpass API response.

    """
    logger.info(f"Querying overpass...\n\n{query}")
    return requests.get(
        OVERPASS_ENDPOINT,
        timeout=query_config.timeout_s + 1,
        params={"data": query},
    )
