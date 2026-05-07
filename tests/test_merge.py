"""Tests for envault.merge."""

from __future__ import annotations

import io
import pytest

from envault.merge import merge_environments, MergeResult
from envault.vault import read_secrets, write_secrets


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    write_secrets(path, "staging", "pass-stg", {"DB_URL": "postgres://stg", "API_KEY": "stg-key", "ONLY_STG": "x"})
    write_secrets(path, "prod", "pass-prd", {"DB_URL": "postgres://prd", "PROD_ONLY": "y"})
    return path


def test_merge_adds_missing_keys(vault_file):
    result = merge_environments(
        vault_file, "staging", "pass-stg", "prod", "pass-prd"
    )
    assert "API_KEY" in result.added
    assert "ONLY_STG" in result.added
    secrets = read_secrets(vault_file, "prod", "pass-prd")
    assert secrets["API_KEY"] == "stg-key"


def test_merge_skips_existing_by_default(vault_file):
    result = merge_environments(
        vault_file, "staging", "pass-stg", "prod", "pass-prd"
    )
    assert "DB_URL" in result.skipped
    secrets = read_secrets(vault_file, "prod", "pass-prd")
    assert secrets["DB_URL"] == "postgres://prd"  # unchanged


def test_merge_overwrite_replaces_existing(vault_file):
    result = merge_environments(
        vault_file, "staging", "pass-stg", "prod", "pass-prd", overwrite=True
    )
    assert "DB_URL" in result.overwritten
    secrets = read_secrets(vault_file, "prod", "pass-prd")
    assert secrets["DB_URL"] == "postgres://stg"


def test_merge_selected_keys_only(vault_file):
    result = merge_environments(
        vault_file, "staging", "pass-stg", "prod", "pass-prd", keys=["API_KEY"]
    )
    assert result.added == ["API_KEY"]
    assert result.skipped == []
    secrets = read_secrets(vault_file, "prod", "pass-prd")
    assert "ONLY_STG" not in secrets


def test_merge_missing_key_raises(vault_file):
    with pytest.raises(KeyError):
        merge_environments(
            vault_file, "staging", "pass-stg", "prod", "pass-prd", keys=["NONEXISTENT"]
        )


def test_merge_returns_merge_result_type(vault_file):
    result = merge_environments(
        vault_file, "staging", "pass-stg", "prod", "pass-prd"
    )
    assert isinstance(result, MergeResult)
    assert isinstance(result.added, list)
    assert isinstance(result.skipped, list)
    assert isinstance(result.overwritten, list)


def test_merge_preserves_dst_only_keys(vault_file):
    merge_environments(vault_file, "staging", "pass-stg", "prod", "pass-prd")
    secrets = read_secrets(vault_file, "prod", "pass-prd")
    assert "PROD_ONLY" in secrets
