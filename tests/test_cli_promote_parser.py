"""Parser-level tests for the promote subcommand."""
import argparse
import pytest
from envault.cli_promote import register_promote_parser


@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    register_promote_parser(sub)
    return p


def test_promote_basic_parses(parser):
    args = parser.parse_args([
        "promote", "my.vault", "dev", "prod",
        "--src-password", "devpw", "--dst-password", "prodpw"
    ])
    assert args.vault == "my.vault"
    assert args.src_env == "dev"
    assert args.dst_env == "prod"
    assert args.src_password == "devpw"
    assert args.dst_password == "prodpw"
    assert args.keys == []
    assert args.overwrite is False


def test_promote_with_keys(parser):
    args = parser.parse_args([
        "promote", "v.json", "staging", "prod",
        "--src-password", "s", "--dst-password", "p",
        "--keys", "DB_URL", "API_KEY"
    ])
    assert args.keys == ["DB_URL", "API_KEY"]


def test_promote_overwrite_flag(parser):
    args = parser.parse_args([
        "promote", "v.json", "staging", "prod",
        "--src-password", "s", "--dst-password", "p",
        "--overwrite"
    ])
    assert args.overwrite is True


def test_promote_missing_passwords_fails(parser):
    with pytest.raises(SystemExit):
        parser.parse_args(["promote", "v.json", "staging", "prod"])


def test_promote_has_func(parser):
    args = parser.parse_args([
        "promote", "v.json", "a", "b",
        "--src-password", "x", "--dst-password", "y"
    ])
    assert callable(args.func)
