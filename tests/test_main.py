"""Test main OSM Scene entrypoint."""

import json
import sys
from unittest import mock

import pytest
import shapely

from osm_scene import DEFAULT_TIMEOUT_S, Response, main, query


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


def test_main_query(dir_io, mock_query_subcommand, monkeypatch):
    polygon = shapely.Polygon([(0, 0), (1, 0), (1, 1)])

    with monkeypatch.context() as m:
        m.delenv("OSM_SCENE_QUERY", raising=False)
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
                    timeout_s=DEFAULT_TIMEOUT_S,
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
                    timeout_s=DEFAULT_TIMEOUT_S,
                ),
            ),
        ],
    )
