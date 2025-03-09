"""Module for building artifacts from Overpass query results."""

from pathlib import Path
from typing import get_args

from pydantic import ConfigDict, Field, computed_field

from osm_scene import (
    DEFAULT_DIR_IO,
    ExistingDirectory,
    WithResponse,
    schemas,
)


class Build(WithResponse):
    """Build artifacts from Overpass query results."""

    model_config = ConfigDict(
        frozen=True,
        validate_default=True,
    )

    dir_in: ExistingDirectory = Field(
        DEFAULT_DIR_IO,
        description="Directory to read Overpass query results.",
    )

    @computed_field
    @property
    def data_in(self) -> list[Path]:
        """Input data files with Overpass query results."""
        return [
            path
            for path in self.dir_in.glob("*.json")
            if path.stem in get_args(schemas.DataType)
        ]

    def cli_cmd(self) -> None:
        """CLI subcommand entrypoint."""
