"""Pytest configuration.

https://docs.pytest.org/en/6.2.x/customize.html

"""

import sys

import pytest


@pytest.fixture
def no_cli_args(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", [])
        yield m
