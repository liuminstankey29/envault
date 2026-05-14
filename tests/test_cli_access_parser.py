"""Tests for the CLI argument parser registration for the access command."""
import argparse
import pytest

from envault.cli_access import register_access_parser


@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="command")
    register_access_parser(sp)
    return p


def test_access_set_parses(parser):
    args = parser.parse_args([
        "access", "set",
        "--vault", "v.env",
        "--environment", "prod",
        "--role", "admin",
        "--readable", "DB_URL", "TOKEN",
        "--writable", "TOKEN",
    ])
    assert args.access_cmd == "set"
    assert args.role == "admin"
    assert "DB_URL" in args.readable
    assert args.writable == ["TOKEN"]


def test_access_set_no_keys_defaults_to_none(parser):
    args = parser.parse_args([
        "access", "set",
        "--vault", "v.env",
        "--environment", "dev",
        "--role", "viewer",
    ])
    assert args.readable is None
    assert args.writable is None


def test_access_remove_parses(parser):
    args = parser.parse_args([
        "access", "remove",
        "--vault", "v.env",
        "--environment", "staging",
        "--role", "ops",
    ])
    assert args.access_cmd == "remove"
    assert args.role == "ops"


def test_access_show_parses(parser):
    args = parser.parse_args([
        "access", "show",
        "--vault", "v.env",
        "--environment", "prod",
        "--role", "dev",
    ])
    assert args.access_cmd == "show"


def test_access_list_parses(parser):
    args = parser.parse_args(["access", "list", "--vault", "v.env"])
    assert args.access_cmd == "list"
    assert args.environment is None


def test_access_list_with_env_filter(parser):
    args = parser.parse_args(["access", "list", "--vault", "v.env", "--environment", "prod"])
    assert args.environment == "prod"


def test_access_check_parses(parser):
    args = parser.parse_args([
        "access", "check",
        "--vault", "v.env",
        "--environment", "prod",
        "--role", "reader",
        "--action", "read",
        "--key", "DB_PASSWORD",
    ])
    assert args.access_cmd == "check"
    assert args.action == "read"
    assert args.key == "DB_PASSWORD"


def test_access_check_invalid_action_rejected(parser):
    with pytest.raises(SystemExit):
        parser.parse_args([
            "access", "check",
            "--vault", "v.env",
            "--environment", "prod",
            "--role", "r",
            "--action", "execute",
            "--key", "K",
        ])
