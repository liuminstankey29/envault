"""Tests for envault.delegate module."""

from __future__ import annotations

import time
import pytest

from envault.delegate import (
    create_delegate,
    list_delegates,
    revoke_delegate,
    validate_delegate,
)


@pytest.fixture()
def vault_file(tmp_path):
    return str(tmp_path / "vault.env")


# --- create_delegate ---

def test_create_delegate_returns_token_string(vault_file):
    token = create_delegate(vault_file, "prod", access="read")
    assert isinstance(token, str)
    assert len(token) > 20


def test_create_delegate_persists_entry(vault_file):
    create_delegate(vault_file, "prod", access="read", label="ci")
    entries = list_delegates(vault_file, "prod")
    assert len(entries) == 1
    assert entries[0].access == "read"
    assert entries[0].label == "ci"


def test_create_delegate_invalid_access_raises(vault_file):
    with pytest.raises(ValueError, match="access must be"):
        create_delegate(vault_file, "prod", access="admin")


def test_multiple_tokens_stored_independently(vault_file):
    create_delegate(vault_file, "prod", access="read")
    create_delegate(vault_file, "prod", access="write")
    entries = list_delegates(vault_file, "prod")
    assert len(entries) == 2
    accesses = {e.access for e in entries}
    assert accesses == {"read", "write"}


# --- validate_delegate ---

def test_validate_returns_true_for_valid_token(vault_file):
    token = create_delegate(vault_file, "staging", access="read")
    assert validate_delegate(vault_file, "staging", token, required_access="read") is True


def test_validate_write_token_satisfies_read_requirement(vault_file):
    token = create_delegate(vault_file, "staging", access="write")
    assert validate_delegate(vault_file, "staging", token, required_access="read") is True


def test_validate_read_token_fails_write_requirement(vault_file):
    token = create_delegate(vault_file, "staging", access="read")
    assert validate_delegate(vault_file, "staging", token, required_access="write") is False


def test_validate_unknown_token_returns_false(vault_file):
    assert validate_delegate(vault_file, "staging", "bogus-token", "read") is False


def test_validate_expired_token_returns_false(vault_file):
    token = create_delegate(vault_file, "prod", access="read", ttl_seconds=-1)
    assert validate_delegate(vault_file, "prod", token, "read") is False


def test_validate_non_expired_token_returns_true(vault_file):
    token = create_delegate(vault_file, "prod", access="read", ttl_seconds=3600)
    assert validate_delegate(vault_file, "prod", token, "read") is True


# --- revoke_delegate ---

def test_revoke_returns_true_when_existed(vault_file):
    token = create_delegate(vault_file, "dev", access="read")
    assert revoke_delegate(vault_file, "dev", token) is True


def test_revoke_removes_token(vault_file):
    token = create_delegate(vault_file, "dev", access="read")
    revoke_delegate(vault_file, "dev", token)
    assert validate_delegate(vault_file, "dev", token, "read") is False


def test_revoke_returns_false_when_not_found(vault_file):
    assert revoke_delegate(vault_file, "dev", "nonexistent") is False


# --- list_delegates ---

def test_list_delegates_empty_when_none(vault_file):
    assert list_delegates(vault_file, "prod") == []


def test_list_delegates_shows_expiry(vault_file):
    create_delegate(vault_file, "prod", access="read", ttl_seconds=60)
    entries = list_delegates(vault_file, "prod")
    assert entries[0].expires_at is not None
    assert entries[0].expires_at > time.time()
