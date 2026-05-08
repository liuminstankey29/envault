"""Tests for envault.cli_pin."""
from __future__ import annotations

import io
import sys
import pytest

from envault.pin import pin_secret
from envault.vault import write_secrets


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture()
def vault_and_env(tmp_path):
    vault = tmp_path / "vault.json"
    password = "testpass"
    write_secrets(str(vault), "prod", password, {"API_KEY": "abc", "DB_PASS": "secret"})
    return str(vault), "prod", password


def test_cmd_pin_add_new(vault_and_env, capsys):
    from envault.cli_pin import cmd_pin

    vault, env, _ = vault_and_env
    args = Args(vault=vault, env=env, key="API_KEY", pin_action="add")
    cmd_pin(args)
    captured = capsys.readouterr()
    assert "Pinned" in captured.out
    assert "API_KEY" in captured.out


def test_cmd_pin_add_already_pinned(vault_and_env, capsys):
    from envault.cli_pin import cmd_pin

    vault, env, _ = vault_and_env
    pin_secret(vault, env, "API_KEY")
    args = Args(vault=vault, env=env, key="API_KEY", pin_action="add")
    cmd_pin(args)
    captured = capsys.readouterr()
    assert "already pinned" in captured.out


def test_cmd_pin_remove_existing(vault_and_env, capsys):
    from envault.cli_pin import cmd_pin

    vault, env, _ = vault_and_env
    pin_secret(vault, env, "DB_PASS")
    args = Args(vault=vault, env=env, key="DB_PASS", pin_action="remove")
    cmd_pin(args)
    captured = capsys.readouterr()
    assert "Unpinned" in captured.out


def test_cmd_pin_remove_not_pinned_exits(vault_and_env):
    from envault.cli_pin import cmd_pin

    vault, env, _ = vault_and_env
    args = Args(vault=vault, env=env, key="API_KEY", pin_action="remove")
    with pytest.raises(SystemExit) as exc:
        cmd_pin(args)
    assert exc.value.code == 1


def test_cmd_pin_status_pinned(vault_and_env, capsys):
    from envault.cli_pin import cmd_pin

    vault, env, _ = vault_and_env
    pin_secret(vault, env, "API_KEY")
    args = Args(vault=vault, env=env, key="API_KEY", pin_action="status")
    cmd_pin(args)
    captured = capsys.readouterr()
    assert "pinned" in captured.out
    assert "not pinned" not in captured.out


def test_cmd_pin_list(vault_and_env, capsys):
    from envault.cli_pin import cmd_pin

    vault, env, _ = vault_and_env
    pin_secret(vault, env, "API_KEY")
    pin_secret(vault, env, "DB_PASS")
    args = Args(vault=vault, env=None, pin_action="list")
    cmd_pin(args)
    captured = capsys.readouterr()
    assert "API_KEY" in captured.out
    assert "DB_PASS" in captured.out
    assert f"[{env}]" in captured.out


def test_cmd_pin_list_empty(vault_and_env, capsys):
    from envault.cli_pin import cmd_pin

    vault, env, _ = vault_and_env
    args = Args(vault=vault, env=None, pin_action="list")
    cmd_pin(args)
    captured = capsys.readouterr()
    assert "No pinned secrets" in captured.out
