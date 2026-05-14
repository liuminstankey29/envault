"""Tests for envault.checksum."""
from __future__ import annotations

import json
import pytest

from envault.vault import write_secrets
from envault.checksum import (
    compute_and_store,
    verify_checksum,
    list_checksums,
    clear_checksum,
)


PASSWORD = "test-pass"
ENV = "production"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    write_secrets(path, ENV, PASSWORD, {"DB_URL": "postgres://localhost", "SECRET": "abc"})
    return path


# ---------------------------------------------------------------------------
# compute_and_store
# ---------------------------------------------------------------------------

def test_compute_and_store_returns_hex_string(vault_file):
    digest = compute_and_store(vault_file, ENV, PASSWORD)
    assert isinstance(digest, str)
    assert len(digest) == 64  # SHA-256 hex


def test_compute_and_store_persists_checksum(vault_file, tmp_path):
    compute_and_store(vault_file, ENV, PASSWORD)
    checksums_path = tmp_path / "vault.checksums.json"
    assert checksums_path.exists()
    data = json.loads(checksums_path.read_text())
    assert ENV in data


def test_compute_and_store_is_deterministic(vault_file):
    d1 = compute_and_store(vault_file, ENV, PASSWORD)
    d2 = compute_and_store(vault_file, ENV, PASSWORD)
    assert d1 == d2


# ---------------------------------------------------------------------------
# verify_checksum
# ---------------------------------------------------------------------------

def test_verify_matches_after_store(vault_file):
    compute_and_store(vault_file, ENV, PASSWORD)
    result = verify_checksum(vault_file, ENV, PASSWORD)
    assert result.matched is True
    assert result.environment == ENV


def test_verify_fails_after_mutation(vault_file):
    compute_and_store(vault_file, ENV, PASSWORD)
    # Mutate secrets
    write_secrets(vault_file, ENV, PASSWORD, {"DB_URL": "postgres://other", "SECRET": "abc"})
    result = verify_checksum(vault_file, ENV, PASSWORD)
    assert result.matched is False


def test_verify_stored_is_none_when_no_checksum_saved(vault_file):
    result = verify_checksum(vault_file, ENV, PASSWORD)
    assert result.stored is None
    assert result.matched is False


# ---------------------------------------------------------------------------
# list_checksums
# ---------------------------------------------------------------------------

def test_list_checksums_empty_when_no_file(vault_file):
    assert list_checksums(vault_file) == {}


def test_list_checksums_shows_all_environments(vault_file):
    write_secrets(vault_file, "staging", "stg-pass", {"KEY": "val"})
    compute_and_store(vault_file, ENV, PASSWORD)
    compute_and_store(vault_file, "staging", "stg-pass")
    result = list_checksums(vault_file)
    assert ENV in result
    assert "staging" in result


# ---------------------------------------------------------------------------
# clear_checksum
# ---------------------------------------------------------------------------

def test_clear_checksum_returns_true_when_existed(vault_file):
    compute_and_store(vault_file, ENV, PASSWORD)
    assert clear_checksum(vault_file, ENV) is True


def test_clear_checksum_returns_false_when_not_present(vault_file):
    assert clear_checksum(vault_file, ENV) is False


def test_clear_checksum_removes_entry(vault_file):
    compute_and_store(vault_file, ENV, PASSWORD)
    clear_checksum(vault_file, ENV)
    assert ENV not in list_checksums(vault_file)
