"""Tests for envault.labels."""
import pytest
from pathlib import Path

from envault.labels import add_label, remove_label, list_labels, filter_by_label


@pytest.fixture()
def vault_file(tmp_path: Path) -> str:
    return str(tmp_path / "vault.env")


def test_add_label_returns_true_when_new(vault_file):
    result = add_label(vault_file, "prod", "DB_PASS", "sensitive")
    assert result.added is True


def test_add_label_returns_false_when_duplicate(vault_file):
    add_label(vault_file, "prod", "DB_PASS", "sensitive")
    result = add_label(vault_file, "prod", "DB_PASS", "sensitive")
    assert result.added is False


def test_add_label_persists(vault_file):
    add_label(vault_file, "prod", "API_KEY", "external")
    mapping = list_labels(vault_file, "prod")
    assert "external" in mapping.get("API_KEY", [])


def test_multiple_labels_on_same_key(vault_file):
    add_label(vault_file, "prod", "SECRET", "sensitive")
    add_label(vault_file, "prod", "SECRET", "external")
    mapping = list_labels(vault_file, "prod")
    assert set(mapping["SECRET"]) == {"sensitive", "external"}


def test_remove_label_returns_true_when_existed(vault_file):
    add_label(vault_file, "prod", "TOKEN", "sensitive")
    result = remove_label(vault_file, "prod", "TOKEN", "sensitive")
    assert result.added is True


def test_remove_label_returns_false_when_missing(vault_file):
    result = remove_label(vault_file, "prod", "TOKEN", "nonexistent")
    assert result.added is False


def test_remove_label_actually_removes(vault_file):
    add_label(vault_file, "prod", "TOKEN", "sensitive")
    remove_label(vault_file, "prod", "TOKEN", "sensitive")
    mapping = list_labels(vault_file, "prod")
    assert "sensitive" not in mapping.get("TOKEN", [])


def test_list_labels_empty_when_no_file(vault_file):
    assert list_labels(vault_file, "prod") == {}


def test_list_labels_filtered_by_key(vault_file):
    add_label(vault_file, "prod", "A", "x")
    add_label(vault_file, "prod", "B", "y")
    result = list_labels(vault_file, "prod", key="A")
    assert "A" in result
    assert "B" not in result


def test_filter_by_label_returns_matching_keys(vault_file):
    add_label(vault_file, "staging", "DB_PASS", "sensitive")
    add_label(vault_file, "staging", "API_KEY", "sensitive")
    add_label(vault_file, "staging", "HOST", "infra")
    keys = filter_by_label(vault_file, "staging", "sensitive")
    assert set(keys) == {"DB_PASS", "API_KEY"}


def test_filter_by_label_returns_empty_when_none_match(vault_file):
    add_label(vault_file, "prod", "X", "other")
    assert filter_by_label(vault_file, "prod", "nonexistent") == []


def test_labels_isolated_per_environment(vault_file):
    add_label(vault_file, "prod", "KEY", "sensitive")
    assert list_labels(vault_file, "staging") == {}
