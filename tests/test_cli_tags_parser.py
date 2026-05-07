"""Tests for register_tags_parser integration."""

from __future__ import annotations

import argparse
import pytest

from envault.cli_tags import register_tags_parser


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    register_tags_parser(sub)
    return p


def test_tags_add_parses(parser):
    args = parser.parse_args(
        ["tags", "--env", "prod", "--password", "pw", "add", "MY_KEY", "mytag"]
    )
    assert args.tags_command == "add"
    assert args.key == "MY_KEY"
    assert args.tag == "mytag"
    assert args.env == "prod"


def test_tags_remove_parses(parser):
    args = parser.parse_args(
        ["tags", "--env", "prod", "--password", "pw", "remove", "MY_KEY", "mytag"]
    )
    assert args.tags_command == "remove"
    assert args.key == "MY_KEY"
    assert args.tag == "mytag"


def test_tags_list_parses(parser):
    args = parser.parse_args(
        ["tags", "--env", "prod", "--password", "pw", "list", "MY_KEY"]
    )
    assert args.tags_command == "list"
    assert args.key == "MY_KEY"


def test_tags_filter_parses(parser):
    args = parser.parse_args(
        ["tags", "--env", "prod", "--password", "pw", "filter", "mytag"]
    )
    assert args.tags_command == "filter"
    assert args.tag == "mytag"
    assert args.reveal is False


def test_tags_filter_reveal_flag(parser):
    args = parser.parse_args(
        ["tags", "--env", "prod", "--password", "pw", "filter", "mytag", "--reveal"]
    )
    assert args.reveal is True


def test_tags_default_vault(parser):
    args = parser.parse_args(
        ["tags", "--env", "prod", "--password", "pw", "list", "KEY"]
    )
    assert args.vault == "vault.enc"


def test_tags_custom_vault(parser):
    args = parser.parse_args(
        ["tags", "--vault", "custom.enc", "--env", "prod", "--password", "pw", "list", "KEY"]
    )
    assert args.vault == "custom.enc"
