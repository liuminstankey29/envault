"""Tests for envault.archive module."""

from __future__ import annotations

import os
import pytest

from envault.vault import write_secrets, read_secrets
from envault.archive import archive_environment, restore_environment, ArchiveResult, RestoreResult


@pytest.fixture
def vault_file(tmp_path):
    path = str(tmp_path / "vault.json")
    write_secrets(path, "prod", "pass", {"DB_URL": "postgres://prod", "TOKEN": "abc"})
    write_secrets(path, "staging", "pass", {"DB_URL": "postgres://staging"})
    return path


def test_archive_returns_result(vault_file, tmp_path):
    out = str(tmp_path / "prod.tar.gz")
    result = archive_environment(vault_file, "prod", "pass", out)
    assert isinstance(result, ArchiveResult)
    assert result.environment == "prod"
    assert result.key_count == 2
    assert result.archive_path == out


def test_archive_creates_file(vault_file, tmp_path):
    out = str(tmp_path / "prod.tar.gz")
    archive_environment(vault_file, "prod", "pass", out)
    assert os.path.isfile(out)


def test_restore_recovers_secrets(vault_file, tmp_path):
    out = str(tmp_path / "prod.tar.gz")
    archive_environment(vault_file, "prod", "pass", out)

    new_vault = str(tmp_path / "new_vault.json")
    result = restore_environment(new_vault, out, "pass")

    assert isinstance(result, RestoreResult)
    assert result.keys_written == 2
    assert result.keys_skipped == 0

    secrets = read_secrets(new_vault, "prod", "pass")
    assert secrets["DB_URL"] == "postgres://prod"
    assert secrets["TOKEN"] == "abc"


def test_restore_skips_existing_by_default(vault_file, tmp_path):
    out = str(tmp_path / "prod.tar.gz")
    archive_environment(vault_file, "prod", "pass", out)

    # staging already has DB_URL
    result = restore_environment(vault_file, out, "pass", target_environment="staging")
    assert "DB_URL" in result.skipped
    assert result.keys_skipped == 1


def test_restore_overwrite_replaces_existing(vault_file, tmp_path):
    out = str(tmp_path / "prod.tar.gz")
    archive_environment(vault_file, "prod", "pass", out)

    result = restore_environment(vault_file, out, "pass", overwrite=True, target_environment="staging")
    assert result.keys_skipped == 0
    secrets = read_secrets(vault_file, "staging", "pass")
    assert secrets["DB_URL"] == "postgres://prod"


def test_restore_target_environment_override(vault_file, tmp_path):
    out = str(tmp_path / "prod.tar.gz")
    archive_environment(vault_file, "prod", "pass", out)

    new_vault = str(tmp_path / "v2.json")
    result = restore_environment(new_vault, out, "pass", target_environment="canary")
    assert result.environment == "canary"
    secrets = read_secrets(new_vault, "canary", "pass")
    assert secrets["TOKEN"] == "abc"


def test_archive_label_stored(vault_file, tmp_path):
    """Label is accepted without error (stored in meta)."""
    out = str(tmp_path / "prod.tar.gz")
    result = archive_environment(vault_file, "prod", "pass", out, label="weekly-backup")
    assert result.archive_path == out
