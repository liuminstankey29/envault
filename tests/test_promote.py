"""Tests for envault.promote."""

import pytest

from envault.vault import write_secrets
from envault.promote import promote_secrets, PromoteResult


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    write_secrets(path, "staging", "s-pass", {"DB_URL": "postgres://staging", "API_KEY": "stg-key", "DEBUG": "true"})
    write_secrets(path, "production", "p-pass", {"DB_URL": "postgres://prod"})
    return path


def test_promote_new_keys(vault_file):
    result = promote_secrets(vault_file, "staging", "s-pass", "production", "p-pass")
    assert "API_KEY" in result.promoted
    assert "DEBUG" in result.promoted


def test_promote_skips_existing_by_default(vault_file):
    result = promote_secrets(vault_file, "staging", "s-pass", "production", "p-pass")
    assert "DB_URL" in result.skipped
    assert "DB_URL" not in result.promoted


def test_promote_overwrite_replaces_existing(vault_file):
    result = promote_secrets(vault_file, "staging", "s-pass", "production", "p-pass", overwrite=True)
    assert "DB_URL" in result.overwritten
    assert "DB_URL" not in result.skipped


def test_promoted_values_readable_in_destination(vault_file):
    from envault.vault import read_secrets
    promote_secrets(vault_file, "staging", "s-pass", "production", "p-pass")
    prod = read_secrets(vault_file, "production", "p-pass")
    assert prod["API_KEY"] == "stg-key"
    assert prod["DEBUG"] == "true"


def test_promote_selected_keys_only(vault_file):
    result = promote_secrets(vault_file, "staging", "s-pass", "production", "p-pass", keys=["API_KEY"])
    assert result.promoted == ["API_KEY"]
    assert "DEBUG" not in result.promoted
    assert "DEBUG" not in result.skipped


def test_promote_missing_key_raises(vault_file):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        promote_secrets(vault_file, "staging", "s-pass", "production", "p-pass", keys=["MISSING_KEY"])


def test_promote_to_new_environment(vault_file):
    from envault.vault import read_secrets
    result = promote_secrets(vault_file, "staging", "s-pass", "canary", "c-pass")
    assert result.total == 3
    canary = read_secrets(vault_file, "canary", "c-pass")
    assert canary["DB_URL"] == "postgres://staging"


def test_result_dataclass_fields(vault_file):
    result = promote_secrets(vault_file, "staging", "s-pass", "production", "p-pass")
    assert isinstance(result, PromoteResult)
    assert result.source == "staging"
    assert result.destination == "production"
    assert isinstance(result.promoted, list)
    assert isinstance(result.skipped, list)
