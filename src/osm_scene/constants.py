"""OSM Scene package constants."""

from typing import Final

from pyproj import Geod

DEFAULT_DIR_IO: Final[str] = "io"
DEFAULT_TIMEOUT_S: Final[int] = 180

GEOD_WGS84: Final[Geod] = Geod(ellps="WGS84")

NDIGITS_DECIMAL_DEGREES: Final[int] = 6
NDIGITS_METERS: Final[int] = 3

OVERPASS_ENDPOINT: Final[str] = "http://overpass-api.de/api/interpreter"
