"""Test build module."""

import pytest
from pydantic import ValidationError

from osm_scene import build


def test_build_dir_in_does_not_exist(tmp_path):
    dir_in = tmp_path / "im-a-directory-but-i-almost-certainly-dont-actually-exist"

    with pytest.raises(ValidationError, match="Existing directory must exist."):
        build.Build(dir_in=dir_in)


def test_build_dir_in_is_not_dir(tmp_path):
    dir_in = tmp_path / "im-not-a-directory.txt"
    dir_in.touch()

    with pytest.raises(
        ValidationError,
        match="Existing directory must be a directory.",
    ):
        build.Build(dir_in=dir_in)


def test_build_data_in(tmp_path):
    dir_in = tmp_path / "dir_in"
    dir_in.mkdir()

    (dir_in / "building.json").touch()
    (dir_in / "null.json").touch()
    (dir_in / "roadway.json").touch()

    b = build.Build(dir_in=dir_in)
    assert set(b.json_paths) == {dir_in / "building.json", dir_in / "roadway.json"}


def test_build_no_data_files(tmp_path):
    dir_in = tmp_path / "dir_in"
    dir_in.mkdir()

    b = build.Build(dir_in=dir_in)
    result = b.cli_cmd()
    assert result is None
    assert b.features == []
    assert b.response().message == f"No data files found in {dir_in}"


def test_build(dir_testdata):
    dir_in = dir_testdata

    b = build.Build(dir_in=dir_in)
    b.cli_cmd()

    assert len(b.features) > 0
    for features in b.features:
        assert len(features.gdf_2d) > 0

    assert b.features[0]
    assert iter(b.features)
