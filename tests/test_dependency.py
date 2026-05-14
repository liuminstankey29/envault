"""Tests for envault.dependency."""
import pytest
from pathlib import Path

from envault.dependency import (
    add_dependency,
    remove_dependency,
    get_dependencies,
    get_dependents,
    transitive_dependents,
    list_all_dependencies,
)


@pytest.fixture
def vault_file(tmp_path: Path) -> str:
    return str(tmp_path / "vault.env")


def test_add_dependency_returns_added_true(vault_file):
    result = add_dependency(vault_file, "prod", "DATABASE_URL", "DB_HOST")
    assert result.added is True
    assert "DB_HOST" in result.depends_on


def test_add_dependency_idempotent(vault_file):
    add_dependency(vault_file, "prod", "DATABASE_URL", "DB_HOST")
    result = add_dependency(vault_file, "prod", "DATABASE_URL", "DB_HOST")
    assert result.added is False
    assert result.depends_on.count("DB_HOST") == 1


def test_add_multiple_dependencies(vault_file):
    add_dependency(vault_file, "prod", "DATABASE_URL", "DB_HOST")
    add_dependency(vault_file, "prod", "DATABASE_URL", "DB_PORT")
    deps = get_dependencies(vault_file, "prod", "DATABASE_URL")
    assert set(deps) == {"DB_HOST", "DB_PORT"}


def test_remove_dependency_returns_removed_true(vault_file):
    add_dependency(vault_file, "prod", "DATABASE_URL", "DB_HOST")
    result = remove_dependency(vault_file, "prod", "DATABASE_URL", "DB_HOST")
    assert result.removed is True
    assert "DB_HOST" not in result.depends_on


def test_remove_nonexistent_dependency_returns_false(vault_file):
    result = remove_dependency(vault_file, "prod", "DATABASE_URL", "DB_HOST")
    assert result.removed is False


def test_get_dependencies_empty_when_none(vault_file):
    assert get_dependencies(vault_file, "prod", "MISSING_KEY") == []


def test_get_dependents_returns_keys_that_depend_on_key(vault_file):
    add_dependency(vault_file, "prod", "DATABASE_URL", "DB_HOST")
    add_dependency(vault_file, "prod", "REPLICA_URL", "DB_HOST")
    dependents = get_dependents(vault_file, "prod", "DB_HOST")
    assert set(dependents) == {"DATABASE_URL", "REPLICA_URL"}


def test_get_dependents_empty_when_no_one_depends(vault_file):
    add_dependency(vault_file, "prod", "DATABASE_URL", "DB_HOST")
    assert get_dependents(vault_file, "prod", "DATABASE_URL") == []


def test_transitive_dependents_single_hop(vault_file):
    add_dependency(vault_file, "prod", "DATABASE_URL", "DB_HOST")
    result = transitive_dependents(vault_file, "prod", "DB_HOST")
    assert result == {"DATABASE_URL"}


def test_transitive_dependents_multi_hop(vault_file):
    # A -> B -> C  means C has transitive dependents A and B
    add_dependency(vault_file, "prod", "A", "B")
    add_dependency(vault_file, "prod", "B", "C")
    result = transitive_dependents(vault_file, "prod", "C")
    assert result == {"A", "B"}


def test_list_all_dependencies_returns_full_map(vault_file):
    add_dependency(vault_file, "prod", "A", "X")
    add_dependency(vault_file, "prod", "B", "Y")
    mapping = list_all_dependencies(vault_file, "prod")
    assert mapping["A"] == ["X"]
    assert mapping["B"] == ["Y"]


def test_environments_are_isolated(vault_file):
    add_dependency(vault_file, "prod", "KEY", "DEP")
    assert get_dependencies(vault_file, "staging", "KEY") == []
