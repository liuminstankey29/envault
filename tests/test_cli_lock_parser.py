"""Tests for register_lock_parser argument parsing."""

import pytest
from argparse import ArgumentParser

from envault.cli_lock import register_lock_parser


@pytest.fixture
def parser():
    p = ArgumentParser()
    subs = p.add_subparsers(dest="command")
    register_lock_parser(subs)
    return p


def test_lock_lock_parses(parser):
    args = parser.parse_args(["lock", "lock", "my.vault", "production"])
    assert args.lock_sub == "lock"
    assert args.vault == "my.vault"
    assert args.environment == "production"
    assert args.reason == ""


def test_lock_lock_with_reason(parser):
    args = parser.parse_args(["lock", "lock", "my.vault", "prod", "--reason", "freeze"])
    assert args.reason == "freeze"


def test_lock_unlock_parses(parser):
    args = parser.parse_args(["lock", "unlock", "my.vault", "staging"])
    assert args.lock_sub == "unlock"
    assert args.environment == "staging"


def test_lock_status_parses(parser):
    args = parser.parse_args(["lock", "status", "my.vault", "dev"])
    assert args.lock_sub == "status"
    assert args.environment == "dev"


def test_lock_list_parses(parser):
    args = parser.parse_args(["lock", "list", "my.vault"])
    assert args.lock_sub == "list"
    assert args.vault == "my.vault"


def test_lock_list_json_flag(parser):
    args = parser.parse_args(["lock", "list", "my.vault", "--json"])
    assert args.json is True


def test_lock_subcommand_required(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["lock"])
