#!/usr/bin/env python3.12
"""Main OSM Scene entrypoint."""

from pydantic_settings import BaseSettings, SettingsConfigDict

from osm_scene import PathField
from osm_scene.query import QueryConfig


class MainConfig(BaseSettings):
    """Primary OSM Scene configuration."""

    model_config = SettingsConfigDict(
        cli_parse_args=True,
        cli_prog_name="osm-scene",
        cli_use_class_docs_for_groups=True,
        env_prefix="OSM_SCENE",
        frozen=True,
    )

    dir_out: PathField

    q: QueryConfig
