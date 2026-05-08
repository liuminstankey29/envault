"""Tests for envault.compare."""
from __future__ import annotations

import pytest

from envault.compare import (
    CompareResult,
    compare_environments,
    format_compare_result,
)
from envault.vault import write_secrets


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.json")
    write_secrets(path, "prod", "pass", {"DB": "prod-db", "API": "prod-api", "SHARED": "same"})
    write_secrets(path, "staging", "pass", {"DB": "stg-db", "CACHE": "redis", "SHARED": "same"})
    return path


def test_only_in_a(vault_file):
    result = compare_environments(vault_file, "prod", "pass", "staging", "pass")
    assert "API" in result.only_in_a


def test_only_in_b(vault_file):
    result = compare_environments(vault_file, "prod", "pass", "staging", "pass")
    assert "CACHE" in result.only_in_b


def test_different_keys(vault_file):
    result = compare_environments(vault_file, "prod", "pass", "staging", "pass")
    assert "DB" in result.different_keys


def test_same_keys(vault_file):
    result = compare_environments(vault_file, "prod", "pass", "staging", "pass")
    assert "SHARED" in result.same_keys


def test_identical_environments(tmp_path):
    path = str(tmp_path / "v.json")
    write_secrets(path, "a", "pw", {"X": "1", "Y": "2"})
    write_secrets(path, "b", "pw", {"X": "1", "Y": "2"})
    result = compare_environments(path, "a", "pw", "b", "pw")
    assert result.is_identical
    assert result.only_in_a == []
    assert result.only_in_b == []
    assert result.different_keys == []


def test_is_identical_false_when_differences(vault_file):
    result = compare_environments(vault_file, "prod", "pass", "staging", "pass")
    assert not result.is_identical


def test_cross_vault_compare(tmp_path):
    va = str(tmp_path / "a.json")
    vb = str(tmp_path / "b.json")
    write_secrets(va, "env", "pw", {"K": "v1"})
    write_secrets(vb, "env", "pw", {"K": "v2"})
    result = compare_environments(va, "env", "pw", "env", "pw", vault_path_b=vb)
    assert "K" in result.different_keys


def test_format_shows_only_in_a(vault_file):
    result = compare_environments(vault_file, "prod", "pass", "staging", "pass")
    output = format_compare_result(result, "prod", "staging")
    assert "API" in output
    assert "Only in [prod]" in output


def test_format_identical_message(tmp_path):
    path = str(tmp_path / "v.json")
    write_secrets(path, "a", "pw", {"X": "1"})
    write_secrets(path, "b", "pw", {"X": "1"})
    result = compare_environments(path, "a", "pw", "b", "pw")
    output = format_compare_result(result, "a", "b")
    assert "identical" in output


def test_format_summary_counts(vault_file):
    result = compare_environments(vault_file, "prod", "pass", "staging", "pass")
    output = format_compare_result(result, "prod", "staging", show_counts=True)
    assert "Summary:" in output


def test_compare_result_defaults():
    r = CompareResult()
    assert r.is_identical
    assert r.same_keys == []
