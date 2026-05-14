"""Tests for register_quota_parser argument parsing."""
from __future__ import annotations

import argparse
import pytest

from envault.cli_quota import register_quota_parser


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    subs = p.add_subparsers(dest="command")
    register_quota_parser(subs)
    return p


def test_quota_set_parses(parser):
    args = parser.parse_args(["quota", "--vault", "v.env", "set", "dev", "20"])
    assert args.quota_sub == "set"
    assert args.environment == "dev"
    assert args.limit == 20


def test_quota_remove_parses(parser):
    args = parser.parse_args(["quota", "--vault", "v.env", "remove", "staging"])
    assert args.quota_sub == "remove"
    assert args.environment == "staging"


def test_quota_status_parses(parser):
    args = parser.parse_args(
        ["quota", "--vault", "v.env", "status", "prod", "--password", "pw"]
    )
    assert args.quota_sub == "status"
    assert args.environment == "prod"
    assert args.password == "pw"


def test_quota_check_parses(parser):
    args = parser.parse_args(
        ["quota", "--vault", "v.env", "check", "dev", "--password", "secret"]
    )
    assert args.quota_sub == "check"
    assert args.environment == "dev"
    assert args.password == "secret"


def test_quota_list_parses(parser):
    args = parser.parse_args(["quota", "--vault", "v.env", "list"])
    assert args.quota_sub == "list"


def test_quota_set_missing_limit_fails(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["quota", "--vault", "v.env", "set", "dev"])


def test_quota_status_missing_password_fails(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["quota", "--vault", "v.env", "status", "dev"])


def test_quota_missing_vault_fails(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["quota", "set", "dev", "10"])
