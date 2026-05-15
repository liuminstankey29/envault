"""Tests for envault.fingerprint."""

import json
from pathlib import Path

import pytest

from envault.vault import write_secrets
from envault.fingerprint import (
    compute_fingerprint,
    get_fingerprint,
    clear_fingerprint,
    _compute_fingerprint,
)


PASSWORD = "fp-test-pw"
ENV = "staging"


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "vault.env"
    write_secrets(str(p), ENV, PASSWORD, {"KEY": "value", "FOO": "bar"})
    return str(p)


def test_compute_fingerprint_returns_hex_string(vault_file):
    result = compute_fingerprint(vault_file, ENV, PASSWORD)
    assert isinstance(result.fingerprint, str)
    assert len(result.fingerprint) == 64  # SHA-256 hex


def test_compute_fingerprint_changed_true_on_first_store(vault_file):
    result = compute_fingerprint(vault_file, ENV, PASSWORD)
    assert result.changed is True
    assert result.previous is None


def test_compute_fingerprint_changed_false_when_unchanged(vault_file):
    compute_fingerprint(vault_file, ENV, PASSWORD)
    result = compute_fingerprint(vault_file, ENV, PASSWORD)
    assert result.changed is False
    assert result.previous == result.fingerprint


def test_compute_fingerprint_changed_true_after_write(vault_file):
    compute_fingerprint(vault_file, ENV, PASSWORD)
    write_secrets(vault_file, ENV, PASSWORD, {"KEY": "value", "FOO": "bar", "NEW": "x"})
    result = compute_fingerprint(vault_file, ENV, PASSWORD)
    assert result.changed is True


def test_store_false_does_not_persist(vault_file):
    compute_fingerprint(vault_file, ENV, PASSWORD, store=False)
    assert get_fingerprint(vault_file, ENV) is None


def test_get_fingerprint_returns_none_before_store(vault_file):
    assert get_fingerprint(vault_file, ENV) is None


def test_get_fingerprint_returns_stored_value(vault_file):
    result = compute_fingerprint(vault_file, ENV, PASSWORD)
    assert get_fingerprint(vault_file, ENV) == result.fingerprint


def test_clear_fingerprint_returns_true_when_existed(vault_file):
    compute_fingerprint(vault_file, ENV, PASSWORD)
    assert clear_fingerprint(vault_file, ENV) is True


def test_clear_fingerprint_returns_false_when_missing(vault_file):
    assert clear_fingerprint(vault_file, ENV) is False


def test_clear_fingerprint_removes_entry(vault_file):
    compute_fingerprint(vault_file, ENV, PASSWORD)
    clear_fingerprint(vault_file, ENV)
    assert get_fingerprint(vault_file, ENV) is None


def test_fingerprint_is_deterministic():
    secrets = {"A": "1", "B": "2"}
    assert _compute_fingerprint(secrets) == _compute_fingerprint(secrets)


def test_fingerprint_order_independent():
    a = {"A": "1", "B": "2"}
    b = {"B": "2", "A": "1"}
    assert _compute_fingerprint(a) == _compute_fingerprint(b)


def test_fingerprints_file_written_next_to_vault(vault_file):
    compute_fingerprint(vault_file, ENV, PASSWORD)
    fp_file = Path(vault_file).with_suffix(".fingerprints.json")
    assert fp_file.exists()
    data = json.loads(fp_file.read_text())
    assert ENV in data
