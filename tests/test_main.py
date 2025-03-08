"""Test main OSM Scene entrypoint."""

import json
import sys
from pathlib import Path
from unittest import mock

import pytest
import shapely

from osm_scene import Response, main, query


@pytest.fixture
def mock_query_subcommand():
    with mock.patch.object(
        query.Query,
        "cli_cmd",
        return_value=None,
    ) as mock_subcommand:
        yield mock_subcommand


def test_main_no_args(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py"])

        with pytest.raises(SystemExit, match="0"):
            main.main()


def test_main_query_cli(dir_io, mock_query_subcommand, monkeypatch):
    polygon = shapely.Polygon([(0, 0), (1, 0), (1, 1)])

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py", "query", "--poly", polygon.wkt])

        response = main.main()

    assert response == Response()
    mock_query_subcommand.assert_has_calls(
        [
            mock.call(
                query.Query(
                    dir_out=dir_io,
                    e2=None,
                    origin=None,
                    poly=polygon,
                ),
            ),
        ],
    )


def test_main_query_env(dir_io, mock_query_subcommand, monkeypatch):
    polygon = shapely.Polygon([(0, 0), (1, 0), (1, 1)])
    query_config = {"poly": polygon.wkt}

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py", "query"])
        m.setenv("OSM_SCENE_QUERY", json.dumps(query_config))

        response = main.main()

    assert response == Response()
    mock_query_subcommand.assert_has_calls(
        [
            mock.call(
                query.Query(
                    dir_out=dir_io,
                    e2=None,
                    origin=None,
                    poly=polygon,
                ),
            ),
        ],
    )


def test_main_query_env_file(dir_io, mock_query_subcommand, monkeypatch):
    polygon = shapely.Polygon([(0, 0), (1, 0), (1, 1)])
    query_config = {"poly": polygon.wkt}

    # save original .env file content before overwriting
    env_file = Path(__file__).parent.parent / ".env"
    original_content = env_file.read_text(encoding="utf-8")
    env_file.write_text(f"OSM_SCENE_QUERY={json.dumps(query_config)}")

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py", "query"])

        response = main.main()

    assert response == Response()
    mock_query_subcommand.assert_has_calls(
        [
            mock.call(
                query.Query(
                    dir_out=dir_io,
                    e2=None,
                    origin=None,
                    poly=polygon,
                ),
            ),
        ],
    )

    # restore original content
    env_file.write_text(original_content)
