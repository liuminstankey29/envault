"""Tests for CLI parser registration of TTL sub-commands."""

from __future__ import annotations

import argparse

import pytest

from envault.cli_ttl import register_ttl_parser


@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    register_ttl_parser(sub)
    return p


def test_ttl_set_parses(parser):
    args = parser.parse_args([
        "ttl", "--environment", "prod",
        "set", "MY_KEY", "2099-01-01T00:00:00+00:00"
    ])
    assert args.ttl_cmd == "set"
    assert args.key == "MY_KEY"
    assert args.expires_at == "2099-01-01T00:00:00+00:00"


def test_ttl_clear_parses(parser):
    args = parser.parse_args(["ttl", "--environment", "staging", "clear", "OLD_KEY"])
    assert args.ttl_cmd == "clear"
    assert args.key == "OLD_KEY"
    assert args.environment == "staging"


def test_ttl_get_parses(parser):
    args = parser.parse_args(["ttl", "--environment", "dev", "get", "TOKEN"])
    assert args.ttl_cmd == "get"
    assert args.key == "TOKEN"


def test_ttl_list_parses(parser):
    args = parser.parse_args(["ttl", "--environment", "prod", "list"])
    assert args.ttl_cmd == "list"


def test_ttl_expired_parses(parser):
    args = parser.parse_args(["ttl", "--environment", "prod", "expired"])
    assert args.ttl_cmd == "expired"


def test_ttl_default_vault(parser):
    args = parser.parse_args(["ttl", "--environment", "prod", "list"])
    assert args.vault == "vault.enc"


def test_ttl_custom_vault(parser):
    args = parser.parse_args(["ttl", "--vault", "custom.enc", "--environment", "prod", "list"])
    assert args.vault == "custom.enc"
