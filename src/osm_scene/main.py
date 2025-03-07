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
        cli_prog_name="osm_scene",
        cli_use_class_docs_for_groups=True,
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_nested_delimiter="__",
        env_prefix="OSM_SCENE_",
        extra="ignore",
        frozen=True,
        nested_model_default_partial_update=True,
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
    return run(MainConfig(_cli_parse_args=True))


if __name__ == "__main__":  # pragma: no cover
    main()
