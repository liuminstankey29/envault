"""Tests for envault.cli_quota cmd_quota."""
from __future__ import annotations

import sys
import pytest

from envault.vault import write_secrets
from envault.quota import set_quota
from envault.cli_quota import cmd_quota


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture()
def vault_and_env(tmp_path):
    p = tmp_path / "vault.env"
    write_secrets(str(p), "dev", "secret", {"A": "1", "B": "2"})
    return str(p)


def test_cmd_quota_set_prints_confirmation(vault_and_env, capsys):
    args = Args(vault=vault_and_env, quota_sub="set", environment="dev", limit=10)
    cmd_quota(args)
    out = capsys.readouterr().out
    assert "dev" in out
    assert "10" in out


def test_cmd_quota_set_invalid_limit_exits_1(vault_and_env):
    args = Args(vault=vault_and_env, quota_sub="set", environment="dev", limit=0)
    with pytest.raises(SystemExit) as exc_info:
        cmd_quota(args)
    assert exc_info.value.code == 1


def test_cmd_quota_remove_existing(vault_and_env, capsys):
    set_quota(vault_and_env, "dev", 5)
    args = Args(vault=vault_and_env, quota_sub="remove", environment="dev")
    cmd_quota(args)
    out = capsys.readouterr().out
    assert "removed" in out.lower()


def test_cmd_quota_remove_nonexistent(vault_and_env, capsys):
    args = Args(vault=vault_and_env, quota_sub="remove", environment="staging")
    cmd_quota(args)
    out = capsys.readouterr().out
    assert "No quota" in out


def test_cmd_quota_status_within_limit(vault_and_env, capsys):
    set_quota(vault_and_env, "dev", 10)
    args = Args(vault=vault_and_env, quota_sub="status", environment="dev", password="secret")
    cmd_quota(args)
    out = capsys.readouterr().out
    assert "Used" in out
    assert "2" in out


def test_cmd_quota_status_exceeded_exits_2(vault_and_env):
    set_quota(vault_and_env, "dev", 1)
    args = Args(vault=vault_and_env, quota_sub="status", environment="dev", password="secret")
    with pytest.raises(SystemExit) as exc_info:
        cmd_quota(args)
    assert exc_info.value.code == 2


def test_cmd_quota_check_passes(vault_and_env, capsys):
    set_quota(vault_and_env, "dev", 10)
    args = Args(vault=vault_and_env, quota_sub="check", environment="dev", password="secret")
    cmd_quota(args)
    out = capsys.readouterr().out
    assert "OK" in out


def test_cmd_quota_check_fails_exits_2(vault_and_env):
    set_quota(vault_and_env, "dev", 1)
    args = Args(vault=vault_and_env, quota_sub="check", environment="dev", password="secret")
    with pytest.raises(SystemExit) as exc_info:
        cmd_quota(args)
    assert exc_info.value.code == 2


def test_cmd_quota_list_shows_entries(vault_and_env, capsys):
    set_quota(vault_and_env, "dev", 10)
    set_quota(vault_and_env, "prod", 50)
    args = Args(vault=vault_and_env, quota_sub="list")
    cmd_quota(args)
    out = capsys.readouterr().out
    assert "dev" in out
    assert "prod" in out


def test_cmd_quota_list_empty(vault_and_env, capsys):
    args = Args(vault=vault_and_env, quota_sub="list")
    cmd_quota(args)
    out = capsys.readouterr().out
    assert "No quotas" in out
