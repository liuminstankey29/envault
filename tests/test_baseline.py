"""Tests for envault.baseline"""

from __future__ import annotations

import pytest

from envault.baseline import (
    BaselineDiff,
    capture_baseline,
    clear_baseline,
    compare_to_baseline,
    load_baseline,
)
from envault.vault import write_secrets


@pytest.fixture
def vault_file(tmp_path):
    path = str(tmp_path / "vault.json")
    write_secrets(path, "production", "pass", {"DB_URL": "postgres://prod", "API_KEY": "abc123"})
    return path


def test_capture_baseline_returns_hashes(vault_file):
    hashes = capture_baseline(vault_file, "production", "pass")
    assert "DB_URL" in hashes
    assert "API_KEY" in hashes
    assert all(len(h) == 64 for h in hashes.values())  # sha256 hex


def test_capture_baseline_persists(vault_file):
    capture_baseline(vault_file, "production", "pass")
    stored = load_baseline(vault_file, "production")
    assert stored is not None
    assert set(stored.keys()) == {"DB_URL", "API_KEY"}


def test_load_baseline_returns_none_when_no_file(vault_file):
    result = load_baseline(vault_file, "staging")
    assert result is None


def test_compare_returns_none_when_no_baseline(vault_file):
    result = compare_to_baseline(vault_file, "production", "pass")
    assert result is None


def test_compare_clean_when_unchanged(vault_file):
    capture_baseline(vault_file, "production", "pass")
    diff = compare_to_baseline(vault_file, "production", "pass")
    assert isinstance(diff, BaselineDiff)
    assert diff.is_clean
    assert set(diff.unchanged) == {"DB_URL", "API_KEY"}


def test_compare_detects_changed_value(vault_file):
    capture_baseline(vault_file, "production", "pass")
    write_secrets(vault_file, "production", "pass", {"DB_URL": "postgres://new", "API_KEY": "abc123"})
    diff = compare_to_baseline(vault_file, "production", "pass")
    assert "DB_URL" in diff.changed
    assert "API_KEY" in diff.unchanged
    assert not diff.is_clean


def test_compare_detects_added_key(vault_file):
    capture_baseline(vault_file, "production", "pass")
    write_secrets(vault_file, "production", "pass", {
        "DB_URL": "postgres://prod", "API_KEY": "abc123", "NEW_KEY": "new"
    })
    diff = compare_to_baseline(vault_file, "production", "pass")
    assert "NEW_KEY" in diff.added
    assert not diff.is_clean


def test_compare_detects_removed_key(vault_file):
    capture_baseline(vault_file, "production", "pass")
    write_secrets(vault_file, "production", "pass", {"DB_URL": "postgres://prod"})
    diff = compare_to_baseline(vault_file, "production", "pass")
    assert "API_KEY" in diff.removed
    assert not diff.is_clean


def test_clear_baseline_returns_true_when_existed(vault_file):
    capture_baseline(vault_file, "production", "pass")
    result = clear_baseline(vault_file, "production")
    assert result is True
    assert load_baseline(vault_file, "production") is None


def test_clear_baseline_returns_false_when_not_found(vault_file):
    result = clear_baseline(vault_file, "nonexistent")
    assert result is False


def test_multiple_environments_independent(vault_file):
    write_secrets(vault_file, "staging", "pass2", {"STAGE_KEY": "val"})
    capture_baseline(vault_file, "production", "pass")
    capture_baseline(vault_file, "staging", "pass2")
    prod = load_baseline(vault_file, "production")
    stage = load_baseline(vault_file, "staging")
    assert "DB_URL" in prod
    assert "STAGE_KEY" in stage
    assert "DB_URL" not in stage
