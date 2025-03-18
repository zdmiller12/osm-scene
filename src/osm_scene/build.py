"""Module for building artifacts from Overpass query results."""

import multiprocessing as mp
from pathlib import Path
from typing import get_args

from loguru import logger
from pydantic import ConfigDict, Field, PrivateAttr, computed_field

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

    _features: schemas.Features = PrivateAttr(default_factory=list)

    @computed_field
    @property
    def json_paths(self) -> list[Path]:
        """Input data files with Overpass query results."""
        return [
            path
            for path in self.dir_in.glob("*.json")
            if path.stem in get_args(schemas.DataType)
        ]

    @property
    def features(self) -> schemas.Features:
        """GeoDataFrames of different data types."""
        return self._features

    def cli_cmd(self) -> None:
        """CLI subcommand entrypoint."""
        logger.info(f"Running query with config={self.model_dump_json(indent=4)}")

        if len(self.json_paths) == 0:
            warning = f"No data files found in {self.dir_in}"
            logger.warning(warning)
            self._response.message = warning
            return

        with mp.Pool(processes=min(len(self.json_paths), mp.cpu_count() - 2)) as pool:
            map_async = pool.map_async(
                schemas.FeatureSet.from_json_path,
                self.json_paths,
            )
            self._features.extend([feature_set.root for feature_set in map_async.get()])
