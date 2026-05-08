"""Tests for envault.alias module."""

import pytest

from envault.alias import (
    set_alias,
    remove_alias,
    resolve_alias,
    list_aliases,
    get_alias_target,
)


@pytest.fixture
def vault_file(tmp_path):
    return str(tmp_path / "test.vault")


def test_set_alias_returns_true_when_new(vault_file):
    assert set_alias(vault_file, "prod", "production") is True


def test_set_alias_returns_false_when_updated(vault_file):
    set_alias(vault_file, "prod", "production")
    assert set_alias(vault_file, "prod", "production-v2") is False


def test_set_alias_persists(vault_file):
    set_alias(vault_file, "dev", "development")
    assert get_alias_target(vault_file, "dev") == "development"


def test_remove_alias_returns_true_when_existed(vault_file):
    set_alias(vault_file, "staging", "staging-env")
    assert remove_alias(vault_file, "staging") is True


def test_remove_alias_returns_false_when_missing(vault_file):
    assert remove_alias(vault_file, "nonexistent") is False


def test_remove_alias_deletes_entry(vault_file):
    set_alias(vault_file, "qa", "qa-env")
    remove_alias(vault_file, "qa")
    assert get_alias_target(vault_file, "qa") is None


def test_resolve_alias_returns_target(vault_file):
    set_alias(vault_file, "p", "production")
    assert resolve_alias(vault_file, "p") == "production"


def test_resolve_alias_returns_name_when_not_alias(vault_file):
    assert resolve_alias(vault_file, "production") == "production"


def test_list_aliases_empty_when_no_file(vault_file):
    assert list_aliases(vault_file) == {}


def test_list_aliases_returns_all(vault_file):
    set_alias(vault_file, "p", "production")
    set_alias(vault_file, "d", "development")
    result = list_aliases(vault_file)
    assert result == {"p": "production", "d": "development"}


def test_get_alias_target_none_when_missing(vault_file):
    assert get_alias_target(vault_file, "missing") is None


def test_multiple_aliases_independent(vault_file):
    set_alias(vault_file, "a", "env-a")
    set_alias(vault_file, "b", "env-b")
    remove_alias(vault_file, "a")
    assert get_alias_target(vault_file, "b") == "env-b"
    assert get_alias_target(vault_file, "a") is None
