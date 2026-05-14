"""Tests for envault.summary."""
from __future__ import annotations

import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta

from envault.vault import write_secrets
from envault.lock import lock_environment
from envault.ttl import set_expiry
from envault.tags import add_tag
from envault.summary import summarise_environment, summarise_all, EnvironmentSummary


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    return tmp_path / "vault.enc"


def _future(days: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past(days: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def test_summary_basic(vault_file):
    write_secrets(vault_file, "prod", "pw", {"A": "1", "B": "2"})
    s = summarise_environment(vault_file, "prod", "pw")
    assert isinstance(s, EnvironmentSummary)
    assert s.environment == "prod"
    assert s.key_count == 2
    assert s.locked is False
    assert s.lock_reason is None
    assert s.expired_keys == []
    assert s.expiring_soon_keys == []


def test_summary_locked_environment(vault_file):
    write_secrets(vault_file, "staging", "pw", {"X": "1"})
    lock_environment(vault_file, "staging", reason="freeze")
    s = summarise_environment(vault_file, "staging", "pw")
    assert s.locked is True


def test_summary_expired_keys(vault_file):
    write_secrets(vault_file, "dev", "pw", {"OLD": "v", "NEW": "v"})
    set_expiry(vault_file, "dev", "OLD", _past(2))
    set_expiry(vault_file, "dev", "NEW", _future(60))
    s = summarise_environment(vault_file, "dev", "pw")
    assert "OLD" in s.expired_keys
    assert "NEW" not in s.expired_keys


def test_summary_expiring_soon_keys(vault_file):
    write_secrets(vault_file, "dev", "pw", {"SOON": "v", "LATER": "v"})
    set_expiry(vault_file, "dev", "SOON", _future(3))
    set_expiry(vault_file, "dev", "LATER", _future(30))
    s = summarise_environment(vault_file, "dev", "pw", warn_days=7)
    assert "SOON" in s.expiring_soon_keys
    assert "LATER" not in s.expiring_soon_keys


def test_summary_tagged_keys(vault_file):
    write_secrets(vault_file, "prod", "pw", {"A": "1", "B": "2", "C": "3"})
    add_tag(vault_file, "prod", "A", "critical")
    add_tag(vault_file, "prod", "B", "critical")
    s = summarise_environment(vault_file, "prod", "pw")
    assert s.tagged_keys == 2


def test_quota_pct_none_when_no_limit(vault_file):
    write_secrets(vault_file, "env", "pw", {"K": "v"})
    s = summarise_environment(vault_file, "env", "pw")
    assert s.quota_pct is None


def test_summarise_all_skips_missing_password(vault_file):
    write_secrets(vault_file, "alpha", "pa", {"K": "v"})
    write_secrets(vault_file, "beta", "pb", {"K": "v"})
    results = summarise_all(vault_file, {"alpha": "pa"})
    envs = [r.environment for r in results]
    assert "alpha" in envs
    assert "beta" not in envs


def test_summarise_all_returns_all_when_passwords_provided(vault_file):
    write_secrets(vault_file, "a", "pa", {"K": "1"})
    write_secrets(vault_file, "b", "pb", {"K": "2"})
    results = summarise_all(vault_file, {"a": "pa", "b": "pb"})
    assert len(results) == 2
