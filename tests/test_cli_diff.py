"""Tests for envault.cli_diff module."""

from __future__ import annotations

import argparse
import io
import sys
from unittest.mock import patch

import pytest

from envault.cli_diff import cmd_diff, register_diff_parser
from envault.vault import write_secrets


class Args:
    """Minimal stand-in for argparse.Namespace."""

    def __init__(self, vault, env_a, env_b, password_a, password_b,
                 show_unchanged=False, reveal=False):
        self.vault = vault
        self.env_a = env_a
        self.env_b = env_b
        self.password_a = password_a
        self.password_b = password_b
        self.show_unchanged = show_unchanged
        self.reveal = reveal


@pytest.fixture()
def vault_and_envs(tmp_path):
    path = str(tmp_path / "vault.json")
    write_secrets(path, "dev", "devpass", {"API_KEY": "dev-key", "COMMON": "same"})
    write_secrets(path, "prod", "prodpass", {"API_KEY": "prod-key", "COMMON": "same", "NEW": "only-prod"})
    return path


def test_cmd_diff_prints_output(vault_and_envs, capsys):
    args = Args(
        vault=vault_and_envs,
        env_a="dev",
        env_b="prod",
        password_a="devpass",
        password_b="prodpass",
    )
    cmd_diff(args)
    captured = capsys.readouterr()
    assert "API_KEY" in captured.out
    assert "NEW" in captured.out


def test_cmd_diff_masks_values_by_default(vault_and_envs, capsys):
    args = Args(
        vault=vault_and_envs,
        env_a="dev",
        env_b="prod",
        password_a="devpass",
        password_b="prodpass",
    )
    cmd_diff(args)
    captured = capsys.readouterr()
    assert "dev-key" not in captured.out
    assert "prod-key" not in captured.out
    assert "***" in captured.out


def test_cmd_diff_reveal_shows_values(vault_and_envs, capsys):
    args = Args(
        vault=vault_and_envs,
        env_a="dev",
        env_b="prod",
        password_a="devpass",
        password_b="prodpass",
        reveal=True,
    )
    cmd_diff(args)
    captured = capsys.readouterr()
    assert "dev-key" in captured.out or "prod-key" in captured.out


def test_cmd_diff_missing_env_exits(vault_and_envs, capsys):
    args = Args(
        vault=vault_and_envs,
        env_a="dev",
        env_b="nonexistent",
        password_a="devpass",
        password_b="wrongpass",
    )
    with pytest.raises(SystemExit) as exc_info:
        cmd_diff(args)
    assert exc_info.value.code == 1


def test_register_diff_parser_adds_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_diff_parser(subparsers)
    args = parser.parse_args(
        ["diff", "dev", "prod", "--vault", "v.json", "--password-a", "p1", "--password-b", "p2"]
    )
    assert args.env_a == "dev"
    assert args.env_b == "prod"
    assert args.vault == "v.json"
    assert args.password_a == "p1"
    assert args.password_b == "p2"
    assert args.show_unchanged is False
    assert args.reveal is False
