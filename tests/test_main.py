"""Test main OSM Scene entrypoint."""

import json
from pathlib import Path

import pytest

from osm_scene import main


@pytest.mark.usefixtures("no_cli_args")
def test_main():
    """Assumes pytest is run from root of the repo."""
    expected_dir_out = Path(__file__).parent.parent

    cfg = main.MainConfig(
        dir_out=".",
        q={
            "e2": (1, 1.1234),
            "origin": (0, 0.1234567),
        },
    )
    assert cfg.dir_out == expected_dir_out
    assert cfg.model_dump() == {
        "dir_out": expected_dir_out,
        "q": {
            "e2": (1.0, 1.1234),
            "origin": (0.0, 0.1234567),
            "poly": None,
        },
    }
    assert cfg.model_dump_json() == json.dumps(
        {
            "dir_out": str(expected_dir_out),
            "q": {
                "e2": [1.0, 1.123],
                "origin": [0.0, 0.123457],
                "poly": None,
            },
        },
        separators=(",", ":"),
    )
