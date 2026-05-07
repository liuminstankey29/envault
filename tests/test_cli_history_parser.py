"""Tests for register_history_parser argument parsing."""
import argparse
import pytest

from envault.cli_history import register_history_parser


@pytest.fixture
def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    register_history_parser(sub)
    return root


def test_history_basic_parses(parser):
    args = parser.parse_args(["history", "my.vault"])
    assert args.vault == "my.vault"
    assert args.env is None
    assert args.key is None
    assert args.action is None
    assert args.limit is None
    assert args.format == "text"


def test_history_env_flag(parser):
    args = parser.parse_args(["history", "v.vault", "--env", "prod"])
    assert args.env == "prod"


def test_history_key_flag(parser):
    args = parser.parse_args(["history", "v.vault", "--key", "DB_PASS"])
    assert args.key == "DB_PASS"


def test_history_action_flag(parser):
    args = parser.parse_args(["history", "v.vault", "--action", "rotate"])
    assert args.action == "rotate"


def test_history_invalid_action_rejected(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["history", "v.vault", "--action", "unknown"])


def test_history_limit_flag(parser):
    args = parser.parse_args(["history", "v.vault", "--limit", "10"])
    assert args.limit == 10


def test_history_json_format(parser):
    args = parser.parse_args(["history", "v.vault", "--format", "json"])
    assert args.format == "json"


def test_history_func_set(parser):
    args = parser.parse_args(["history", "v.vault"])
    from envault.cli_history import cmd_history
    assert args.func is cmd_history
