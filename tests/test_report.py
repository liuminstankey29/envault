"""Tests for envault.report module."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import write_secrets
from envault.report import (
    build_environment_report,
    build_vault_report,
    EnvironmentReport,
    VaultReport,
)


@pytest.fixture
def vault_file(tmp_path):
    return tmp_path / "vault.env"


def _write(vault_file, env, pw, secrets):
    write_secrets(vault_file, env, pw, secrets)


def test_report_basic_secret_count(vault_file):
    _write(vault_file, "prod", "pw", {"A": "1", "B": "2"})
    rep = build_environment_report(vault_file, "prod", "pw")
    assert rep.secret_count == 2
    assert rep.environment == "prod"


def test_report_not_locked_by_default(vault_file):
    _write(vault_file, "prod", "pw", {"X": "y"})
    rep = build_environment_report(vault_file, "prod", "pw")
    assert rep.locked is False


def test_report_locked_environment(vault_file):
    from envault.lock import lock_environment
    _write(vault_file, "staging", "pw", {"K": "v"})
    lock_environment(vault_file, "staging")
    rep = build_environment_report(vault_file, "staging", "pw")
    assert rep.locked is True


def test_report_lint_errors_for_empty_value(vault_file):
    _write(vault_file, "dev", "pw", {"EMPTY": ""})
    rep = build_environment_report(vault_file, "dev", "pw")
    assert rep.lint_errors >= 1


def test_report_no_lint_errors_clean(vault_file):
    _write(vault_file, "dev", "pw", {"KEY": "value"})
    rep = build_environment_report(vault_file, "dev", "pw")
    assert rep.lint_errors == 0


def test_report_expired_keys(vault_file):
    from datetime import datetime, timezone, timedelta
    from envault.ttl import set_expiry
    _write(vault_file, "prod", "pw", {"OLD": "v", "NEW": "v"})
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    set_expiry(vault_file, "prod", "OLD", past)
    rep = build_environment_report(vault_file, "prod", "pw")
    assert "OLD" in rep.expired_keys
    assert "NEW" not in rep.expired_keys


def test_vault_report_aggregates_environments(vault_file):
    _write(vault_file, "prod", "pw", {"A": "1", "B": "2"})
    _write(vault_file, "dev", "pw", {"C": "3"})
    rep = build_vault_report(vault_file, {"prod": "pw", "dev": "pw"})
    assert isinstance(rep, VaultReport)
    assert rep.total_secrets == 3
    assert len(rep.environments) == 2


def test_vault_report_bad_password_graceful(vault_file):
    _write(vault_file, "prod", "correct", {"A": "1"})
    rep = build_vault_report(vault_file, {"prod": "wrong"})
    env_rep = next(e for e in rep.environments if e.environment == "prod")
    assert env_rep.secret_count == 0


def test_vault_report_quota_pct(vault_file):
    from envault.quota import set_quota
    _write(vault_file, "prod", "pw", {"A": "1", "B": "2"})
    set_quota(vault_file, "prod", 10)
    rep = build_environment_report(vault_file, "prod", "pw")
    assert rep.quota_pct is not None
    assert rep.quota_pct == 20.0
