"""Parser-level tests for the broadcast subcommand."""
from __future__ import annotations

import argparse

import pytest

from envault.cli_broadcast import register_broadcast_parser


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    register_broadcast_parser(sub)
    return root


def test_broadcast_add_parses(parser):
    args = parser.parse_args(["broadcast", "--vault", "v.env", "add", "https://example.com"])
    assert args.broadcast_cmd == "add"
    assert args.url == "https://example.com"
    assert args.events is None


def test_broadcast_add_with_events(parser):
    args = parser.parse_args([
        "broadcast", "--vault", "v.env",
        "add", "https://example.com",
        "--events", "secret.changed", "secret.rotated",
    ])
    assert args.events == ["secret.changed", "secret.rotated"]


def test_broadcast_remove_parses(parser):
    args = parser.parse_args(["broadcast", "--vault", "v.env", "remove", "https://example.com"])
    assert args.broadcast_cmd == "remove"
    assert args.url == "https://example.com"


def test_broadcast_list_parses(parser):
    args = parser.parse_args(["broadcast", "--vault", "v.env", "list"])
    assert args.broadcast_cmd == "list"


def test_broadcast_send_parses(parser):
    args = parser.parse_args([
        "broadcast", "--vault", "v.env",
        "send", "secret.changed",
        "--environment", "production",
        "--note", "manual trigger",
    ])
    assert args.broadcast_cmd == "send"
    assert args.event == "secret.changed"
    assert args.environment == "production"
    assert args.note == "manual trigger"


def test_broadcast_send_defaults(parser):
    args = parser.parse_args(["broadcast", "--vault", "v.env", "send", "any.event"])
    assert args.environment == ""
    assert args.note == ""


def test_broadcast_missing_vault_fails(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["broadcast", "add", "https://example.com"])
