"""Test main OSM Scene entrypoint."""

import json
import sys
from pathlib import Path

import pytest
import shapely

from osm_scene import main


def test_main_no_args(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py"])

        with pytest.raises(SystemExit, match="0"):
            main.main()


def test_main_query_cli(monkeypatch):
    polygon = shapely.Polygon([(0, 0), (1, 0), (1, 1)])

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py", "query", "--poly", polygon.wkt])

        response = main.main()
        assert response == main.MainResponse()


def test_main_query_env(monkeypatch):
    polygon = shapely.Polygon([(0, 0), (1, 0), (1, 1)])

    query_config = {"poly": polygon.wkt}

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py", "query"])

        m.setenv("OSM_SCENE_QUERY", json.dumps(query_config))

        response = main.main()
        assert response == main.MainResponse()


def test_main_query_env_file(monkeypatch):
    polygon = shapely.Polygon([(0, 0), (1, 0), (1, 1)])

    query_config = {"poly": polygon.wkt}

    env_file_dir = Path(__file__).parent.parent
    env_file = env_file_dir / ".env"

    original_content = env_file.read_text(encoding="utf-8")
    env_file.write_text(f"OSM_SCENE_QUERY={json.dumps(query_config)}")

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py", "query"])

        response = main.main()
        assert response == main.MainResponse()

    env_file.write_text(original_content)
