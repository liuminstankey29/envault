"""Tests for envault.promote."""
import pytest
from pathlib import Path
from envault.vault import write_secrets, read_secrets
from envault.promote import promote_secrets, PromoteResult


@pytest.fixture
def vault_file(tmp_path):
    return str(tmp_path / "vault.json")


def test_promote_new_keys(vault_file):
    write_secrets(vault_file, "staging", "s3cr3t", {"DB_URL": "postgres://staging", "API_KEY": "abc"})
    write_secrets(vault_file, "production", "pr0d", {})
    result = promote_secrets(vault_file, "staging", "production", "s3cr3t", "pr0d")
    assert "DB_URL" in result.promoted
    assert "API_KEY" in result.promoted
    assert result.skipped == []
    assert result.overwritten == []


def test_promote_skips_existing_by_default(vault_file):
    write_secrets(vault_file, "staging", "s3cr3t", {"DB_URL": "postgres://staging", "NEW_KEY": "new"})
    write_secrets(vault_file, "production", "pr0d", {"DB_URL": "postgres://prod"})
    result = promote_secrets(vault_file, "staging", "production", "s3cr3t", "pr0d")
    assert "DB_URL" in result.skipped
    assert "NEW_KEY" in result.promoted
    prod = read_secrets(vault_file, "production", "pr0d")
    assert prod["DB_URL"] == "postgres://prod"  # unchanged


def test_promote_overwrite_replaces_existing(vault_file):
    write_secrets(vault_file, "staging", "s3cr3t", {"DB_URL": "postgres://staging"})
    write_secrets(vault_file, "production", "pr0d", {"DB_URL": "postgres://prod"})
    result = promote_secrets(vault_file, "staging", "production", "s3cr3t", "pr0d", overwrite=True)
    assert "DB_URL" in result.overwritten
    prod = read_secrets(vault_file, "production", "pr0d")
    assert prod["DB_URL"] == "postgres://staging"


def test_promoted_values_readable_in_destination(vault_file):
    write_secrets(vault_file, "staging", "s3cr3t", {"TOKEN": "tok123"})
    write_secrets(vault_file, "production", "pr0d", {})
    promote_secrets(vault_file, "staging", "production", "s3cr3t", "pr0d")
    prod = read_secrets(vault_file, "production", "pr0d")
    assert prod["TOKEN"] == "tok123"


def test_promote_selected_keys_only(vault_file):
    write_secrets(vault_file, "staging", "s3cr3t", {"A": "1", "B": "2", "C": "3"})
    write_secrets(vault_file, "production", "pr0d", {})
    result = promote_secrets(vault_file, "staging", "production", "s3cr3t", "pr0d", keys=["A", "C"])
    assert set(result.promoted) == {"A", "C"}
    prod = read_secrets(vault_file, "production", "pr0d")
    assert "B" not in prod


def test_promote_missing_key_raises(vault_file):
    write_secrets(vault_file, "staging", "s3cr3t", {"A": "1"})
    write_secrets(vault_file, "production", "pr0d", {})
    with pytest.raises(KeyError, match="MISSING"):
        promote_secrets(vault_file, "staging", "production", "s3cr3t", "pr0d", keys=["MISSING"])


def test_total_counts_promoted_and_overwritten(vault_file):
    write_secrets(vault_file, "staging", "s3cr3t", {"A": "1", "B": "2", "C": "3"})
    write_secrets(vault_file, "production", "pr0d", {"B": "old"})
    result = promote_secrets(vault_file, "staging", "production", "s3cr3t", "pr0d", overwrite=True)
    assert result.total == 3
