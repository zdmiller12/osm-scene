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

import json
import multiprocessing as mp
import re
from functools import cached_property
from pathlib import Path
from typing import Self, get_args

import requests
from loguru import logger
from pydantic import ConfigDict, Field, model_validator
from pyproj.aoi import BBox

from osm_scene import (
    DEFAULT_DIR_IO,
    DEFAULT_TIMEOUT_S,
    GEOD_WGS84,
    OVERPASS_ENDPOINT,
    Extent2D,
    LatLon,
    PathField,
    SimplePoly,
    WithResponse,
    schemas,
)

REGEX_OVERPASS_TIMEOUT = re.compile(
    r"(?<=\[timeout:)\d+\.?\d*",
    flags=re.MULTILINE,
)


class Query(WithResponse):
    """Query public Overpass API for data."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
        validate_default=True,
    )

    dir_out: PathField = Field(
        DEFAULT_DIR_IO,
        description="Directory for saving Overpass query results as JSON files.",
    )

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
        DEFAULT_TIMEOUT_S,
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
        """Get Overpass query string for buildings.

        TODO:
            Get building relations.

        """
        return f"""
            [out:json][timeout:{self.timeout_s}];
            way["building"]{self.area_filter};
            out tags geom;
        """

    def get_roadway_query(self) -> str:
        """Get Overpass query string for roadways."""
        return f"""
            [out:json][timeout:{self.timeout_s}];
            (
                // "major"
                way[highway~"^(motorway|trunk|primary|secondary|tertiary|(motorway|trunk|primary|secondary)_link)$"]{self.area_filter};

                // "minor"
                way[highway~"^(unclassified|residential|living_street|service|pedestrian|track)$"]{self.area_filter};
            );
            out tags geom;
        """

    def get_output_path(self, data_type: schemas.DataType) -> Path:
        """Get output file path for `data_type`."""
        return self.dir_out / f"{data_type}.json"

    def get_queries(self) -> dict[Path, str]:
        """Get all Overpass queries for data."""
        return {
            self.get_output_path(data_type): get_query()
            for data_type in get_args(schemas.DataType)
            if (get_query := getattr(self, f"get_{data_type}_query", None)) is not None
        }

    def cli_cmd(self) -> None:
        """CLI subcommand entrypoint."""
        logger.info(f"Running query with config={self.model_dump_json(indent=4)}")

        queries = self.get_queries()
        with mp.Pool(processes=min(len(queries), mp.cpu_count() - 2)) as pool:
            starmap_async = pool.starmap_async(
                get_data,
                queries.items(),
                callback=_get_data_callback,
            )
            output_paths = [
                result
                for result in starmap_async.get(timeout=self.timeout_s + 3)
                if isinstance(result, Path)
            ]

        self._response.output["output_paths"] = output_paths


def _get_data_callback(output_paths: list[Path]) -> None:
    """Log saved paths from multiprocessing pool."""
    for output_path in output_paths:
        logger.info(f"Saved {output_path=}")


def get_data(output_path: Path, overpass_query: str) -> Path | None:
    """Get data from Overpass.

    `overpass_query` should be specific to a single data type, which will be used to
    query the public Overpass API and results written to `output_path`.

    Parameters
    ----------
    output_path : Path
        Output file path for Overpass results.
    overpass_query : str
        Query string for Overpass API.

    Returns
    -------
    Path
        Output file path with Overpass results, or None if unable to get data.

    """
    response = query_overpass(overpass_query)

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.error(e)
        return None
    else:
        output_path.parent.mkdir(exist_ok=True, parents=True)
        with output_path.open("w") as file:
            json.dump(response.json(), file, indent=4)
        return output_path


def query_overpass(query: str) -> requests.Response:
    """Query Overpass.

    Parameters
    ----------
    query : str
        Query string.

    Returns
    -------
    requests.Response
        Overpass API response.

    """
    logger.info(f"Querying {OVERPASS_ENDPOINT=} with\n{query}")

    try:
        overpass_timeout = int(REGEX_OVERPASS_TIMEOUT.search(query).group(0))
    except AttributeError:
        overpass_timeout = DEFAULT_TIMEOUT_S

    return requests.get(
        OVERPASS_ENDPOINT,
        timeout=overpass_timeout + 1,
        params={"data": query},
    )
