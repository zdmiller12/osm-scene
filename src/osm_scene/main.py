#!/usr/bin/env python3.12
"""Main OSM Scene entrypoint."""

from loguru import logger
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from osm_scene import PathField
from osm_scene.query import QueryConfig


class MainConfig(BaseSettings):
    """Primary OSM Scene configuration."""

    model_config = SettingsConfigDict(
        cli_parse_args=True,
        cli_prog_name="osm-scene",
        cli_use_class_docs_for_groups=True,
        env_prefix="OSM_SCENE_",
        frozen=True,
    )

    dir_out: PathField = "."

    q: QueryConfig


class MainResponse(BaseModel):
    """Response model."""


def run(cfg: MainConfig) -> MainResponse:
    """Run primary process.

    Args:
        cfg (MainConfig): Execution configuration.

    Returns
    -------
        Response with relevant information.

    """
    logger.info(f"Running with config...\n{cfg.model_dump_json(indent=4)}")
    response = MainResponse()

    # do stuff
    logger.info(f"Response {response.model_dump_json(indent=4)}")

    return response


def main() -> MainResponse:
    """Primary entrypoint."""
    return run(MainConfig(_cli_enforce_required=True))


if __name__ == "__main__":  # pragma: no cover
    main()
