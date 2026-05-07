"""Tests for envault.ttl module."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.ttl import (
    clear_expiry,
    get_expiry,
    list_all_expiries,
    list_expired,
    set_expiry,
)


@pytest.fixture
def vault_file(tmp_path):
    return str(tmp_path / "vault.enc")


def _future(days=1):
    return datetime.now(tz=timezone.utc) + timedelta(days=days)


def _past(days=1):
    return datetime.now(tz=timezone.utc) - timedelta(days=days)


def test_set_expiry_creates_ttl_file(vault_file, tmp_path):
    set_expiry(vault_file, "prod", "API_KEY", _future())
    ttl_file = tmp_path / "vault.ttl.json"
    assert ttl_file.exists()


def test_set_and_get_expiry_roundtrip(vault_file):
    exp = _future(3)
    set_expiry(vault_file, "prod", "DB_PASS", exp)
    result = get_expiry(vault_file, "prod", "DB_PASS")
    assert result is not None
    assert abs((result - exp).total_seconds()) < 1


def test_get_expiry_returns_none_when_not_set(vault_file):
    assert get_expiry(vault_file, "prod", "MISSING_KEY") is None


def test_clear_expiry_removes_entry(vault_file):
    set_expiry(vault_file, "prod", "TOKEN", _future())
    removed = clear_expiry(vault_file, "prod", "TOKEN")
    assert removed is True
    assert get_expiry(vault_file, "prod", "TOKEN") is None


def test_clear_expiry_returns_false_when_not_set(vault_file):
    assert clear_expiry(vault_file, "prod", "GHOST") is False


def test_list_expired_returns_only_past_keys(vault_file):
    set_expiry(vault_file, "prod", "OLD_KEY", _past(2))
    set_expiry(vault_file, "prod", "NEW_KEY", _future(2))
    expired = list_expired(vault_file, "prod")
    assert "OLD_KEY" in expired
    assert "NEW_KEY" not in expired


def test_list_expired_empty_when_none_expired(vault_file):
    set_expiry(vault_file, "staging", "FRESH", _future(10))
    assert list_expired(vault_file, "staging") == []


def test_list_all_expiries_returns_all(vault_file):
    set_expiry(vault_file, "dev", "A", _future(1))
    set_expiry(vault_file, "dev", "B", _future(2))
    result = list_all_expiries(vault_file, "dev")
    assert set(result.keys()) == {"A", "B"}


def test_multiple_environments_isolated(vault_file):
    set_expiry(vault_file, "prod", "KEY", _past())
    set_expiry(vault_file, "dev", "KEY", _future())
    assert "KEY" in list_expired(vault_file, "prod")
    assert "KEY" not in list_expired(vault_file, "dev")


def test_set_expiry_overwrites_existing(vault_file):
    old = _past(1)
    new = _future(5)
    set_expiry(vault_file, "prod", "SECRET", old)
    set_expiry(vault_file, "prod", "SECRET", new)
    result = get_expiry(vault_file, "prod", "SECRET")
    assert result > datetime.now(tz=timezone.utc)
