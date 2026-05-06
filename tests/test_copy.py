"""Tests for envault.copy module."""

from __future__ import annotations

import pytest

from envault.copy import copy_secrets
from envault.vault import read_secrets, write_secrets


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.json")
    write_secrets(path, "staging", "pass-staging", {"DB_URL": "postgres://staging", "API_KEY": "stg-key"})
    write_secrets(path, "prod", "pass-prod", {"DB_URL": "postgres://prod"})
    return path


def test_copy_all_secrets(vault_file):
    result = copy_secrets(vault_file, "staging", "qa", "pass-staging", "pass-qa")
    assert result["copied"] == 2
    assert result["skipped"] == 0
    secrets = read_secrets(vault_file, "qa", "pass-qa")
    assert secrets["DB_URL"] == "postgres://staging"
    assert secrets["API_KEY"] == "stg-key"


def test_copy_selected_keys(vault_file):
    result = copy_secrets(
        vault_file, "staging", "qa", "pass-staging", "pass-qa", keys=["API_KEY"]
    )
    assert result["copied"] == 1
    secrets = read_secrets(vault_file, "qa", "pass-qa")
    assert "API_KEY" in secrets
    assert "DB_URL" not in secrets


def test_missing_key_raises(vault_file):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        copy_secrets(
            vault_file, "staging", "qa", "pass-staging", "pass-qa", keys=["MISSING_KEY"]
        )


def test_no_overwrite_skips_existing_keys(vault_file):
    result = copy_secrets(
        vault_file,
        "staging",
        "prod",
        "pass-staging",
        "pass-prod",
        overwrite=False,
    )
    assert result["skipped"] == 1  # DB_URL already in prod
    assert result["copied"] == 1  # API_KEY is new
    secrets = read_secrets(vault_file, "prod", "pass-prod")
    assert secrets["DB_URL"] == "postgres://prod"  # unchanged


def test_overwrite_replaces_existing_keys(vault_file):
    copy_secrets(vault_file, "staging", "prod", "pass-staging", "pass-prod", overwrite=True)
    secrets = read_secrets(vault_file, "prod", "pass-prod")
    assert secrets["DB_URL"] == "postgres://staging"


def test_copy_to_new_environment(vault_file):
    result = copy_secrets(vault_file, "staging", "newenv", "pass-staging", "pass-newenv")
    assert result["copied"] == 2
    secrets = read_secrets(vault_file, "newenv", "pass-newenv")
    assert len(secrets) == 2


def test_copy_returns_zero_when_nothing_to_copy(vault_file):
    # Copy staging -> prod with no-overwrite; then copy again — everything should be skipped
    copy_secrets(vault_file, "staging", "prod", "pass-staging", "pass-prod", overwrite=True)
    result = copy_secrets(
        vault_file, "staging", "prod", "pass-staging", "pass-prod", overwrite=False
    )
    assert result["copied"] == 0
    assert result["skipped"] == 2
