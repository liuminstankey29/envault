"""Tests for envault.cli_lock module."""

import json
import pytest
from io import StringIO
from unittest.mock import patch

from envault.cli_lock import cmd_lock
from envault.lock import lock_environment, is_locked


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.env")


def test_cmd_lock_locks_environment(vault_path, capsys):
    args = Args(lock_sub="lock", vault=vault_path, environment="production", reason="")
    cmd_lock(args)
    assert is_locked(vault_path, "production")
    out = capsys.readouterr().out
    assert "Locked" in out
    assert "production" in out


def test_cmd_lock_with_reason_shown(vault_path, capsys):
    args = Args(lock_sub="lock", vault=vault_path, environment="prod", reason="code freeze")
    cmd_lock(args)
    out = capsys.readouterr().out
    assert "code freeze" in out


def test_cmd_unlock_removes_lock(vault_path, capsys):
    lock_environment(vault_path, "staging")
    args = Args(lock_sub="unlock", vault=vault_path, environment="staging")
    cmd_lock(args)
    assert not is_locked(vault_path, "staging")
    out = capsys.readouterr().out
    assert "Unlocked" in out


def test_cmd_unlock_not_locked_message(vault_path, capsys):
    args = Args(lock_sub="unlock", vault=vault_path, environment="dev")
    cmd_lock(args)
    out = capsys.readouterr().out
    assert "not locked" in out


def test_cmd_status_locked(vault_path, capsys):
    lock_environment(vault_path, "prod", reason="freeze")
    args = Args(lock_sub="status", vault=vault_path, environment="prod")
    cmd_lock(args)
    out = capsys.readouterr().out
    assert "LOCKED" in out
    assert "freeze" in out


def test_cmd_status_unlocked(vault_path, capsys):
    args = Args(lock_sub="status", vault=vault_path, environment="dev")
    cmd_lock(args)
    out = capsys.readouterr().out
    assert "UNLOCKED" in out


def test_cmd_list_empty(vault_path, capsys):
    args = Args(lock_sub="list", vault=vault_path, json=False)
    cmd_lock(args)
    out = capsys.readouterr().out
    assert "No environments" in out


def test_cmd_list_json_output(vault_path, capsys):
    lock_environment(vault_path, "prod", reason="hold")
    args = Args(lock_sub="list", vault=vault_path, json=True)
    cmd_lock(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "prod" in data
