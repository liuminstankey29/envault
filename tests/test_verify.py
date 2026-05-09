"""Tests for envault.verify."""

from __future__ import annotations

import os
import tempfile

import pytest

from envault.vault import write_secrets
from envault.verify import VerifyResult, checksum_of, verify_secrets


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    write_secrets(path, "prod", "hunter2", {"API_KEY": "abc123", "DB_PASS": "secret"})
    return path


def test_verify_clean_returns_ok(vault_file):
    result = verify_secrets(vault_file, "prod", "hunter2")
    assert isinstance(result, VerifyResult)
    assert result.ok
    assert result.error_count == 0


def test_verify_required_keys_present(vault_file):
    result = verify_secrets(vault_file, "prod", "hunter2", required_keys=["API_KEY", "DB_PASS"])
    assert result.ok


def test_verify_required_key_missing(vault_file):
    result = verify_secrets(vault_file, "prod", "hunter2", required_keys=["MISSING_KEY"])
    assert not result.ok
    assert result.error_count == 1
    assert result.issues[0].key == "MISSING_KEY"
    assert "missing" in result.issues[0].reason


def test_verify_required_key_empty(tmp_path):
    path = str(tmp_path / "vault.enc")
    write_secrets(path, "dev", "pw", {"EMPTY_KEY": ""})
    result = verify_secrets(path, "dev", "pw", required_keys=["EMPTY_KEY"])
    assert not result.ok
    assert "empty" in result.issues[0].reason


def test_verify_checksum_passes(vault_file):
    checksums = {"API_KEY": checksum_of("abc123")}
    result = verify_secrets(vault_file, "prod", "hunter2", expected_checksums=checksums)
    assert result.ok


def test_verify_checksum_mismatch(vault_file):
    checksums = {"API_KEY": checksum_of("wrong_value")}
    result = verify_secrets(vault_file, "prod", "hunter2", expected_checksums=checksums)
    assert not result.ok
    assert result.error_count == 1
    assert "mismatch" in result.issues[0].reason


def test_verify_checksum_key_not_found(vault_file):
    checksums = {"NONEXISTENT": checksum_of("value")}
    result = verify_secrets(vault_file, "prod", "hunter2", expected_checksums=checksums)
    assert not result.ok
    assert result.issues[0].key == "NONEXISTENT"


def test_verify_combined_required_and_checksum(vault_file):
    checksums = {"DB_PASS": checksum_of("secret")}
    result = verify_secrets(
        vault_file,
        "prod",
        "hunter2",
        expected_checksums=checksums,
        required_keys=["API_KEY", "DB_PASS"],
    )
    assert result.ok
    assert result.error_count == 0


def test_checksum_of_is_deterministic():
    assert checksum_of("hello") == checksum_of("hello")
    assert checksum_of("hello") != checksum_of("world")


def test_verify_error_count_and_warning_count(vault_file):
    result = verify_secrets(vault_file, "prod", "hunter2", required_keys=["MISSING_A", "MISSING_B"])
    assert result.error_count == 2
    assert result.warning_count == 0
    assert not result.ok
