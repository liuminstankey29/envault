"""Tests for the argparse registration of the schema sub-command."""
from __future__ import annotations

import argparse

import pytest

from envault.cli_schema import register_schema_parser


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    register_schema_parser(sub)
    return p


def test_schema_basic_parses(parser):
    args = parser.parse_args(
        ["schema", "vault.json", "prod", "schema.json", "--password", "secret"]
    )
    assert args.vault == "vault.json"
    assert args.env == "prod"
    assert args.schema == "schema.json"
    assert args.password == "secret"
    assert args.format == "text"


def test_schema_json_format_flag(parser):
    args = parser.parse_args(
        ["schema", "v.json", "staging", "s.json", "--password", "pw", "--format", "json"]
    )
    assert args.format == "json"


def test_schema_invalid_format_rejected(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["schema", "v.json", "prod", "s.json", "--password", "pw", "--format", "xml"]
        )


def test_schema_missing_password_rejected(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["schema", "v.json", "prod", "s.json"])


def test_schema_func_set(parser):
    args = parser.parse_args(
        ["schema", "v.json", "prod", "s.json", "--password", "pw"]
    )
    assert callable(args.func)
