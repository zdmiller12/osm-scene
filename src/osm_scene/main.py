#!/usr/bin/env python3.12
"""Main OSM Scene entrypoint."""

import sys

from loguru import logger
from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliSubCommand,
    SettingsConfigDict,
)

from osm_scene import Response, WithResponse, build, query

logger.bind(name="osm_scene")


class MainConfig(BaseSettings, WithResponse):
    """OSM Scene CLI application."""

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
    )

    build: CliSubCommand[build.Build]
    query: CliSubCommand[query.Query]

    def cli_cmd(self) -> None:
        """Run main application."""
        if len(sys.argv) == 1:
            CliApp.run(self.__class__, cli_args=["--help"])

        subcommand = CliApp.run_subcommand(self)
        self._response = subcommand.response()


def main() -> Response:
    """Primary entrypoint."""
    command = CliApp.run(MainConfig)
    return command.response()


if __name__ == "__main__":  # pragma: no cover
    main()
