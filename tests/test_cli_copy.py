"""Tests for envault.cli_copy module."""

from __future__ import annotations

import sys
import pytest

from envault.cli_copy import cmd_copy
from envault.vault import write_secrets, read_secrets


class Args:
    def __init__(self, **kwargs):
        defaults = {
            "vault": "",
            "src_env": "staging",
            "dst_env": "prod",
            "src_password": "src-pass",
            "dst_password": "dst-pass",
            "keys": [],
            "no_overwrite": False,
        }
        defaults.update(kwargs)
        self.__dict__.update(defaults)


@pytest.fixture()
def vault_and_envs(tmp_path):
    path = str(tmp_path / "vault.json")
    write_secrets(path, "staging", "src-pass", {"SECRET": "value", "TOKEN": "tok"})
    write_secrets(path, "prod", "dst-pass", {})
    return path


def test_cmd_copy_prints_summary(vault_and_envs, capsys):
    args = Args(vault=vault_and_envs)
    cmd_copy(args)
    out = capsys.readouterr().out
    assert "Copied 2 secret(s)" in out
    assert "staging" in out
    assert "prod" in out


def test_cmd_copy_skipped_shown(vault_and_envs, capsys):
    # Copy once, then copy again with no-overwrite
    args = Args(vault=vault_and_envs)
    cmd_copy(args)
    args2 = Args(vault=vault_and_envs, no_overwrite=True)
    cmd_copy(args2)
    out = capsys.readouterr().out
    assert "2 skipped" in out


def test_cmd_copy_missing_key_exits(vault_and_envs, capsys):
    args = Args(vault=vault_and_envs, keys=["DOES_NOT_EXIST"])
    with pytest.raises(SystemExit) as exc_info:
        cmd_copy(args)
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "DOES_NOT_EXIST" in err


def test_cmd_copy_secrets_readable_after_copy(vault_and_envs):
    args = Args(vault=vault_and_envs)
    cmd_copy(args)
    secrets = read_secrets(vault_and_envs, "prod", "dst-pass")
    assert secrets["SECRET"] == "value"
    assert secrets["TOKEN"] == "tok"


def test_cmd_copy_specific_keys_only(vault_and_envs, capsys):
    args = Args(vault=vault_and_envs, keys=["TOKEN"])
    cmd_copy(args)
    secrets = read_secrets(vault_and_envs, "prod", "dst-pass")
    assert "TOKEN" in secrets
    assert "SECRET" not in secrets
