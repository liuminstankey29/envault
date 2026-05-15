"""Tests for the CLI argument parser for the report command."""
from __future__ import annotations

import argparse
import pytest

from envault.cli_report import register_report_parser


@pytest.fixture
def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    register_report_parser(sub)
    return root


def test_report_basic_parses(parser):
    args = parser.parse_args(["report", "vault.env", "--password", "pw"])
    assert args.vault == "vault.env"
    assert args.password == "pw"
    assert args.environment is None
    assert args.format == "text"


def test_report_env_flag(parser):
    args = parser.parse_args(["report", "v.env", "--password", "pw", "--env", "prod"])
    assert args.environment == "prod"


def test_report_json_format_flag(parser):
    args = parser.parse_args(["report", "v.env", "--password", "pw", "--format", "json"])
    assert args.format == "json"


def test_report_invalid_format_rejected(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["report", "v.env", "--password", "pw", "--format", "xml"])


def test_report_missing_password_rejected(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["report", "v.env"])


def test_report_sets_func(parser):
    from envault.cli_report import cmd_report
    args = parser.parse_args(["report", "v.env", "--password", "pw"])
    assert args.func is cmd_report
