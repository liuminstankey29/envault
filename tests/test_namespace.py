"""Tests for envault.namespace."""
from __future__ import annotations

import pytest

from envault.vault import write_secrets
from envault.namespace import (
    assign_namespace,
    get_namespace,
    list_namespace_keys,
    remove_namespace,
    _namespace_path,
)


@pytest.fixture
def vault_file(tmp_path):
    p = tmp_path / "vault.enc"
    write_secrets(str(p), "dev", "pass", {"DB_URL": "postgres://", "API_KEY": "abc123", "SECRET": "xyz"})
    return str(p)


def test_assign_namespace_returns_result(vault_file):
    result = assign_namespace(vault_file, "dev", "pass", "database", ["DB_URL"])
    assert result.namespace == "database"
    assert "DB_URL" in result.keys_affected
    assert result.total == 1


def test_assign_namespace_persists(vault_file):
    assign_namespace(vault_file, "dev", "pass", "database", ["DB_URL"])
    ns = get_namespace(vault_file, "dev", "DB_URL")
    assert ns == "database"


def test_assign_skips_missing_vault_keys(vault_file):
    result = assign_namespace(vault_file, "dev", "pass", "misc", ["NONEXISTENT"])
    assert result.total == 0
    assert result.keys_affected == []


def test_assign_skips_already_assigned_without_overwrite(vault_file):
    assign_namespace(vault_file, "dev", "pass", "ns1", ["API_KEY"])
    result = assign_namespace(vault_file, "dev", "pass", "ns2", ["API_KEY"])
    assert "API_KEY" in result.already_assigned
    assert get_namespace(vault_file, "dev", "API_KEY") == "ns1"


def test_assign_overwrite_replaces_namespace(vault_file):
    assign_namespace(vault_file, "dev", "pass", "ns1", ["API_KEY"])
    result = assign_namespace(vault_file, "dev", "pass", "ns2", ["API_KEY"], overwrite=True)
    assert "API_KEY" in result.keys_affected
    assert get_namespace(vault_file, "dev", "API_KEY") == "ns2"


def test_get_namespace_returns_none_when_unassigned(vault_file):
    assert get_namespace(vault_file, "dev", "SECRET") is None


def test_list_namespace_keys_returns_correct_secrets(vault_file):
    assign_namespace(vault_file, "dev", "pass", "database", ["DB_URL"])
    assign_namespace(vault_file, "dev", "pass", "auth", ["API_KEY", "SECRET"])
    db_keys = list_namespace_keys(vault_file, "dev", "pass", "database")
    assert list(db_keys.keys()) == ["DB_URL"]
    assert db_keys["DB_URL"] == "postgres://"


def test_list_namespace_empty_when_no_assignments(vault_file):
    result = list_namespace_keys(vault_file, "dev", "pass", "nonexistent")
    assert result == {}


def test_remove_namespace_clears_assignment(vault_file):
    assign_namespace(vault_file, "dev", "pass", "database", ["DB_URL"])
    cleared = remove_namespace(vault_file, "dev", ["DB_URL"])
    assert "DB_URL" in cleared
    assert get_namespace(vault_file, "dev", "DB_URL") is None


def test_remove_namespace_returns_only_cleared_keys(vault_file):
    assign_namespace(vault_file, "dev", "pass", "auth", ["API_KEY"])
    cleared = remove_namespace(vault_file, "dev", ["API_KEY", "UNASSIGNED_KEY"])
    assert cleared == ["API_KEY"]
