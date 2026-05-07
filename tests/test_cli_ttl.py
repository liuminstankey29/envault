"""Tests for envault.cli_ttl module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from envault.cli_ttl import cmd_ttl
from envault.ttl import get_expiry, set_expiry


class Args:
    def __init__(self, **kwargs):
        self.vault = kwargs.get("vault", "vault.enc")
        self.environment = kwargs.get("environment", "prod")
        self.ttl_cmd = kwargs.get("ttl_cmd", "list")
        self.key = kwargs.get("key", "")
        self.expires_at = kwargs.get("expires_at", "")


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.enc")


def _future_iso(days=1):
    return (datetime.now(tz=timezone.utc) + timedelta(days=days)).isoformat()


def _past_iso(days=1):
    return (datetime.now(tz=timezone.utc) - timedelta(days=days)).isoformat()


def test_cmd_ttl_set(vault_path, capsys):
    args = Args(vault=vault_path, ttl_cmd="set", key="API_KEY", expires_at=_future_iso(5))
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert get_expiry(vault_path, "prod", "API_KEY") is not None


def test_cmd_ttl_set_invalid_date_exits(vault_path):
    args = Args(vault=vault_path, ttl_cmd="set", key="K", expires_at="not-a-date")
    with pytest.raises(SystemExit):
        cmd_ttl(args)


def test_cmd_ttl_get_shows_active(vault_path, capsys):
    exp = datetime.now(tz=timezone.utc) + timedelta(days=3)
    set_expiry(vault_path, "prod", "DB_PASS", exp)
    args = Args(vault=vault_path, ttl_cmd="get", key="DB_PASS")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "active" in out


def test_cmd_ttl_get_shows_expired(vault_path, capsys):
    exp = datetime.now(tz=timezone.utc) - timedelta(days=1)
    set_expiry(vault_path, "prod", "OLD", exp)
    args = Args(vault=vault_path, ttl_cmd="get", key="OLD")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "EXPIRED" in out


def test_cmd_ttl_get_missing_key(vault_path, capsys):
    args = Args(vault=vault_path, ttl_cmd="get", key="GHOST")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "No expiry" in out


def test_cmd_ttl_clear(vault_path, capsys):
    exp = datetime.now(tz=timezone.utc) + timedelta(days=2)
    set_expiry(vault_path, "prod", "TOKEN", exp)
    args = Args(vault=vault_path, ttl_cmd="clear", key="TOKEN")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "cleared" in out
    assert get_expiry(vault_path, "prod", "TOKEN") is None


def test_cmd_ttl_list_empty(vault_path, capsys):
    args = Args(vault=vault_path, ttl_cmd="list")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "No expiries" in out


def test_cmd_ttl_expired_lists_keys(vault_path, capsys):
    set_expiry(vault_path, "prod", "STALE", datetime.now(tz=timezone.utc) - timedelta(hours=1))
    args = Args(vault=vault_path, ttl_cmd="expired")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "STALE" in out
