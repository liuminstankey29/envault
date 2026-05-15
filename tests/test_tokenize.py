"""Tests for envault.tokenize."""
import pytest
from pathlib import Path
from envault.tokenize import (
    create_token,
    resolve_token,
    revoke_token,
    list_tokens,
)


@pytest.fixture
def vault_file(tmp_path):
    return str(tmp_path / "vault.env")


def test_create_token_returns_result(vault_file):
    result = create_token(vault_file, "production", "DB_PASSWORD")
    assert result.environment == "production"
    assert result.key == "DB_PASSWORD"
    assert result.token.startswith("tok_")
    assert result.created is True


def test_create_token_idempotent(vault_file):
    r1 = create_token(vault_file, "production", "DB_PASSWORD")
    r2 = create_token(vault_file, "production", "DB_PASSWORD")
    assert r1.token == r2.token
    assert r2.created is False


def test_tokens_are_unique_per_key(vault_file):
    r1 = create_token(vault_file, "production", "DB_PASSWORD")
    r2 = create_token(vault_file, "production", "API_KEY")
    assert r1.token != r2.token


def test_tokens_are_unique_per_environment(vault_file):
    r1 = create_token(vault_file, "staging", "DB_PASSWORD")
    r2 = create_token(vault_file, "production", "DB_PASSWORD")
    assert r1.token != r2.token


def test_resolve_token_returns_env_and_key(vault_file):
    result = create_token(vault_file, "production", "SECRET")
    resolved = resolve_token(vault_file, result.token)
    assert resolved == ("production", "SECRET")


def test_resolve_unknown_token_returns_none(vault_file):
    assert resolve_token(vault_file, "tok_nonexistent") is None


def test_revoke_token_returns_true_when_existed(vault_file):
    create_token(vault_file, "production", "DB_PASSWORD")
    assert revoke_token(vault_file, "production", "DB_PASSWORD") is True


def test_revoke_token_returns_false_when_missing(vault_file):
    assert revoke_token(vault_file, "production", "NONEXISTENT") is False


def test_revoke_token_makes_it_unresolvable(vault_file):
    result = create_token(vault_file, "production", "DB_PASSWORD")
    revoke_token(vault_file, "production", "DB_PASSWORD")
    assert resolve_token(vault_file, result.token) is None


def test_list_tokens_returns_all_keys(vault_file):
    create_token(vault_file, "staging", "KEY_A")
    create_token(vault_file, "staging", "KEY_B")
    tokens = list_tokens(vault_file, "staging")
    assert set(tokens.keys()) == {"KEY_A", "KEY_B"}
    for v in tokens.values():
        assert v.startswith("tok_")


def test_list_tokens_empty_when_no_environment(vault_file):
    assert list_tokens(vault_file, "nonexistent") == {}


def test_tokens_file_created_on_disk(vault_file, tmp_path):
    create_token(vault_file, "production", "X")
    token_file = tmp_path / "vault.tokens.json"
    assert token_file.exists()
