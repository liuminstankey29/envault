"""Tests for envault.cli_alias module."""

import sys
import pytest

from envault.alias import set_alias
from envault.cli_alias import cmd_alias


class Args:
    def __init__(self, vault, alias_action, **kwargs):
        self.vault = vault
        self.alias_action = alias_action
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "test.vault")


def test_cmd_alias_set_new(vault_path, capsys):
    args = Args(vault_path, "set", alias="p", environment="production")
    cmd_alias(args)
    out = capsys.readouterr().out
    assert "Created" in out
    assert "'p'" in out
    assert "'production'" in out


def test_cmd_alias_set_update(vault_path, capsys):
    set_alias(vault_path, "p", "production")
    args = Args(vault_path, "set", alias="p", environment="production-v2")
    cmd_alias(args)
    out = capsys.readouterr().out
    assert "Updated" in out


def test_cmd_alias_remove_existing(vault_path, capsys):
    set_alias(vault_path, "dev", "development")
    args = Args(vault_path, "remove", alias="dev")
    cmd_alias(args)
    out = capsys.readouterr().out
    assert "Removed" in out


def test_cmd_alias_remove_missing_exits(vault_path):
    args = Args(vault_path, "remove", alias="ghost")
    with pytest.raises(SystemExit) as exc:
        cmd_alias(args)
    assert exc.value.code == 1


def test_cmd_alias_resolve_known(vault_path, capsys):
    set_alias(vault_path, "s", "staging")
    args = Args(vault_path, "resolve", alias="s")
    cmd_alias(args)
    assert capsys.readouterr().out.strip() == "staging"


def test_cmd_alias_resolve_passthrough(vault_path, capsys):
    args = Args(vault_path, "resolve", alias="production")
    cmd_alias(args)
    assert capsys.readouterr().out.strip() == "production"


def test_cmd_alias_list_empty(vault_path, capsys):
    args = Args(vault_path, "list")
    cmd_alias(args)
    assert "No aliases" in capsys.readouterr().out


def test_cmd_alias_list_shows_entries(vault_path, capsys):
    set_alias(vault_path, "p", "production")
    set_alias(vault_path, "d", "development")
    args = Args(vault_path, "list")
    cmd_alias(args)
    out = capsys.readouterr().out
    assert "p" in out and "production" in out
    assert "d" in out and "development" in out


def test_cmd_alias_get_missing_exits(vault_path):
    args = Args(vault_path, "get", alias="nope")
    with pytest.raises(SystemExit) as exc:
        cmd_alias(args)
    assert exc.value.code == 1


def test_cmd_alias_get_existing(vault_path, capsys):
    set_alias(vault_path, "qa", "qa-env")
    args = Args(vault_path, "get", alias="qa")
    cmd_alias(args)
    assert capsys.readouterr().out.strip() == "qa-env"
