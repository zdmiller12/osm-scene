"""Test main OSM Scene entrypoint."""

import json
import sys
from pathlib import Path

import pytest
import shapely
from pydantic import ValidationError

from osm_scene import main


@pytest.mark.usefixtures("no_cli_args")
def test_main_config():
    """Assumes pytest is run from root of the repo."""
    expected_dir_out = Path(__file__).parent.parent

    cfg = main.MainConfig(
        dir_out=".",
        q={
            "e2": (1, 1.1234),
            "origin": (0, 0.1234567),
            "timeout_s": 900,
        },
    )
    assert cfg.dir_out == expected_dir_out
    assert cfg.model_dump() == {
        "dir_out": expected_dir_out,
        "q": {
            "e2": (1.0, 1.1234),
            "origin": (0.0, 0.1234567),
            "poly": None,
            "timeout_s": 900,
        },
    }
    assert cfg.model_dump_json() == json.dumps(
        {
            "dir_out": str(expected_dir_out),
            "q": {
                "e2": [1.0, 1.123],
                "origin": [0.0, 0.123457],
                "poly": None,
                "timeout_s": 900,
            },
        },
        separators=(",", ":"),
    )


def test_main_no_args(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py"])

        with pytest.raises(ValidationError, match="Field required "):
            main.main()


def test_main_cli(monkeypatch):
    polygon = shapely.Polygon([(0, 0), (1, 0), (1, 1)])

    query_config = {"poly": polygon.wkt}

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py", "--q", json.dumps(query_config)])

        response = main.main()
        assert response == main.MainResponse()


def test_main_env(monkeypatch):
    polygon = shapely.Polygon([(0, 0), (1, 0), (1, 1)])

    query_config = {"poly": polygon.wkt}

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py"])

        m.setenv("OSM_SCENE_Q", json.dumps(query_config))

        response = main.main()
        assert response == main.MainResponse()


def test_main_env_file(monkeypatch):
    polygon = shapely.Polygon([(0, 0), (1, 0), (1, 1)])

    query_config = {"poly": polygon.wkt}

    env_file_dir = Path(__file__).parent.parent
    env_file = env_file_dir / ".env"

    original_content = env_file.read_text(encoding="utf-8")
    env_file.write_text(f"OSM_SCENE_Q={json.dumps(query_config)}")

    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["main.py"])

        response = main.main()
        assert response == main.MainResponse()

    env_file.write_text(original_content)
