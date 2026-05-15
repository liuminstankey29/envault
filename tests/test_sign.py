"""Tests for envault.sign."""

from __future__ import annotations

import json
import pytest

from envault.vault import write_secrets
from envault.sign import (
    sign_environment,
    verify_environment,
    list_signed_environments,
    _sign_path,
)


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "vault.enc"
    write_secrets(str(p), "prod", {"API_KEY": "abc123", "DB_PASS": "secret"}, "pw")
    write_secrets(str(p), "staging", {"API_KEY": "xyz789"}, "pw2")
    return str(p)


def test_sign_returns_signature_string(vault_file):
    result = sign_environment(vault_file, "prod", "pw", "sigkey")
    assert isinstance(result.signature, str)
    assert len(result.signature) == 64  # SHA-256 hex


def test_sign_updated_true_on_first_sign(vault_file):
    result = sign_environment(vault_file, "prod", "pw", "sigkey")
    assert result.updated is True


def test_sign_updated_false_when_unchanged(vault_file):
    sign_environment(vault_file, "prod", "pw", "sigkey")
    result = sign_environment(vault_file, "prod", "pw", "sigkey")
    assert result.updated is False


def test_sign_persists_to_sigs_file(vault_file):
    sign_environment(vault_file, "prod", "pw", "sigkey")
    sig_path = _sign_path(vault_file)
    assert sig_path.exists()
    data = json.loads(sig_path.read_text())
    assert "prod" in data


def test_verify_valid_after_sign(vault_file):
    sign_environment(vault_file, "prod", "pw", "sigkey")
    result = verify_environment(vault_file, "prod", "pw", "sigkey")
    assert result.valid is True


def test_verify_invalid_when_no_signature(vault_file):
    result = verify_environment(vault_file, "prod", "pw", "sigkey")
    assert result.valid is False
    assert result.expected is None


def test_verify_invalid_after_secret_change(vault_file):
    sign_environment(vault_file, "prod", "pw", "sigkey")
    # Overwrite a secret so the signature no longer matches
    write_secrets(vault_file, "prod", {"API_KEY": "CHANGED", "DB_PASS": "secret"}, "pw")
    result = verify_environment(vault_file, "prod", "pw", "sigkey")
    assert result.valid is False
    assert result.expected != result.actual


def test_verify_invalid_with_wrong_signing_key(vault_file):
    sign_environment(vault_file, "prod", "pw", "sigkey")
    result = verify_environment(vault_file, "prod", "pw", "wrong-key")
    assert result.valid is False


def test_list_signed_environments_empty_before_any_sign(vault_file):
    assert list_signed_environments(vault_file) == []


def test_list_signed_environments_after_signing(vault_file):
    sign_environment(vault_file, "prod", "pw", "sigkey")
    sign_environment(vault_file, "staging", "pw2", "sigkey")
    envs = list_signed_environments(vault_file)
    assert set(envs) == {"prod", "staging"}


def test_different_signing_keys_produce_different_signatures(vault_file):
    r1 = sign_environment(vault_file, "prod", "pw", "key-a")
    r2 = sign_environment(vault_file, "prod", "pw", "key-b")
    assert r1.signature != r2.signature
