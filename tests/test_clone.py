"""Tests for envault.clone."""

from __future__ import annotations

import pytest

from envault.vault import read_secrets, write_secrets
from envault.clone import clone_environment, CloneResult


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    write_secrets(path, "prod", "prod-pass", {"DB_URL": "postgres://prod", "API_KEY": "abc123", "TIMEOUT": "30"})
    write_secrets(path, "staging", "stg-pass", {"DB_URL": "postgres://staging"})
    return path


def test_clone_all_secrets(vault_file):
    result = clone_environment(vault_file, "prod", "prod-pass", "dev", "dev-pass")
    assert isinstance(result, CloneResult)
    assert result.copied == 3
    assert result.skipped == 0
    assert result.overwritten == 0
    secrets = read_secrets(vault_file, "dev", "dev-pass")
    assert secrets["DB_URL"] == "postgres://prod"
    assert secrets["API_KEY"] == "abc123"


def test_clone_selected_keys(vault_file):
    result = clone_environment(
        vault_file, "prod", "prod-pass", "dev2", "dev2-pass", keys=["API_KEY"]
    )
    assert result.copied == 1
    secrets = read_secrets(vault_file, "dev2", "dev2-pass")
    assert "API_KEY" in secrets
    assert "DB_URL" not in secrets


def test_clone_skips_existing_by_default(vault_file):
    result = clone_environment(vault_file, "prod", "prod-pass", "staging", "stg-pass")
    assert result.skipped == 1  # DB_URL already exists
    assert result.copied == 2
    # Original value preserved
    secrets = read_secrets(vault_file, "staging", "stg-pass")
    assert secrets["DB_URL"] == "postgres://staging"


def test_clone_overwrite_replaces_existing(vault_file):
    result = clone_environment(
        vault_file, "prod", "prod-pass", "staging", "stg-pass", overwrite=True
    )
    assert result.overwritten == 1
    secrets = read_secrets(vault_file, "staging", "stg-pass")
    assert secrets["DB_URL"] == "postgres://prod"


def test_clone_missing_key_raises(vault_file):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        clone_environment(
            vault_file, "prod", "prod-pass", "dev", "dev-pass", keys=["MISSING_KEY"]
        )


def test_clone_result_total(vault_file):
    result = clone_environment(vault_file, "prod", "prod-pass", "staging", "stg-pass", overwrite=True)
    assert result.total == result.copied + result.skipped + result.overwritten


def test_clone_creates_new_environment(vault_file):
    clone_environment(vault_file, "prod", "prod-pass", "brand-new", "new-pass")
    secrets = read_secrets(vault_file, "brand-new", "new-pass")
    assert len(secrets) == 3
