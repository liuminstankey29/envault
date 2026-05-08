"""Tests for envault.prune."""

import os
import pytest
from datetime import datetime, timezone, timedelta

from envault.vault import write_secrets, read_secrets
from envault.ttl import set_expiry
from envault.prune import prune_expired, prune_keys, PruneResult


PASSWORD = "testpass"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    write_secrets(path, "production", PASSWORD, {"DB_URL": "postgres://", "API_KEY": "abc", "SECRET": "xyz"})
    return path


def _past() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=1)


def _future() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=1)


# ---------------------------------------------------------------------------
# prune_expired
# ---------------------------------------------------------------------------

def test_prune_expired_removes_expired_key(vault_file):
    set_expiry(vault_file, "production", "API_KEY", _past())
    result = prune_expired(vault_file, "production", PASSWORD)
    assert "API_KEY" in result.removed
    assert "API_KEY" not in read_secrets(vault_file, "production", PASSWORD)


def test_prune_expired_keeps_valid_key(vault_file):
    set_expiry(vault_file, "production", "DB_URL", _future())
    set_expiry(vault_file, "production", "API_KEY", _past())
    result = prune_expired(vault_file, "production", PASSWORD)
    assert "DB_URL" in result.kept
    assert "DB_URL" in read_secrets(vault_file, "production", PASSWORD)


def test_prune_expired_dry_run_does_not_modify(vault_file):
    set_expiry(vault_file, "production", "SECRET", _past())
    result = prune_expired(vault_file, "production", PASSWORD, dry_run=True)
    assert "SECRET" in result.removed
    # vault unchanged
    assert "SECRET" in read_secrets(vault_file, "production", PASSWORD)


def test_prune_expired_no_expired_returns_empty_removed(vault_file):
    result = prune_expired(vault_file, "production", PASSWORD)
    assert result.removed == []
    assert result.total_kept == 3


def test_prune_expired_returns_prune_result_type(vault_file):
    result = prune_expired(vault_file, "production", PASSWORD)
    assert isinstance(result, PruneResult)


# ---------------------------------------------------------------------------
# prune_keys
# ---------------------------------------------------------------------------

def test_prune_keys_removes_specified(vault_file):
    result = prune_keys(vault_file, "production", PASSWORD, ["DB_URL", "SECRET"])
    assert set(result.removed) == {"DB_URL", "SECRET"}
    remaining = read_secrets(vault_file, "production", PASSWORD)
    assert "DB_URL" not in remaining
    assert "SECRET" not in remaining
    assert "API_KEY" in remaining


def test_prune_keys_ignores_missing_keys(vault_file):
    result = prune_keys(vault_file, "production", PASSWORD, ["NONEXISTENT"])
    assert result.removed == []
    assert result.total_kept == 3


def test_prune_keys_dry_run_does_not_modify(vault_file):
    result = prune_keys(vault_file, "production", PASSWORD, ["API_KEY"], dry_run=True)
    assert "API_KEY" in result.removed
    assert "API_KEY" in read_secrets(vault_file, "production", PASSWORD)


def test_prune_result_totals(vault_file):
    set_expiry(vault_file, "production", "API_KEY", _past())
    result = prune_expired(vault_file, "production", PASSWORD)
    assert result.total_removed == 1
    assert result.total_kept == 2
