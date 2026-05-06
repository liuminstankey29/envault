"""Tests for envault.search and envault.cli_search."""

from __future__ import annotations

import json
import os
import tempfile
from io import StringIO
from unittest.mock import patch

import pytest

from envault.search import SearchResult, format_search_results, search_secrets
from envault.vault import write_secrets


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "test.vault")
    write_secrets(path, "production", "secret123", {"DB_HOST": "prod.db", "DB_PASS": "s3cr3t"})
    write_secrets(path, "staging", "secret123", {"DB_HOST": "stage.db", "API_KEY": "abc123"})
    write_secrets(path, "dev", "secret123", {"DEBUG": "true", "API_KEY": "devkey"})
    return path


def test_search_by_key_pattern(vault_file):
    results = search_secrets(vault_file, "secret123", key_pattern="DB_*")
    keys = [(r.environment, r.key) for r in results]
    assert ("production", "DB_HOST") in keys
    assert ("production", "DB_PASS") in keys
    assert ("staging", "DB_HOST") in keys
    assert all(r.key.startswith("DB_") for r in results)


def test_search_by_value_substring(vault_file):
    results = search_secrets(vault_file, "secret123", value_substring=".db")
    keys = [(r.environment, r.key) for r in results]
    assert ("production", "DB_HOST") in keys
    assert ("staging", "DB_HOST") in keys
    assert len(results) == 2


def test_search_combined_pattern_and_value(vault_file):
    results = search_secrets(vault_file, "secret123", key_pattern="API_KEY", value_substring="abc")
    assert len(results) == 1
    assert results[0].environment == "staging"
    assert results[0].key == "API_KEY"


def test_search_limited_to_environments(vault_file):
    results = search_secrets(
        vault_file, "secret123", key_pattern="API_KEY", environments=["dev"]
    )
    assert len(results) == 1
    assert results[0].environment == "dev"


def test_search_values_hidden_by_default(vault_file):
    results = search_secrets(vault_file, "secret123", key_pattern="DB_HOST")
    assert all(r.value is None for r in results)


def test_search_values_shown_when_requested(vault_file):
    results = search_secrets(vault_file, "secret123", key_pattern="DB_HOST", show_values=True)
    assert all(r.value is not None for r in results)


def test_search_no_criteria_raises():
    with pytest.raises(ValueError, match="At least one"):
        search_secrets("any.vault", "pw")


def test_format_results_empty():
    assert format_search_results([]) == "No matches found."


def test_format_results_groups_by_env():
    results = [
        SearchResult("production", "DB_HOST", None),
        SearchResult("production", "DB_PASS", None),
        SearchResult("staging", "DB_HOST", None),
    ]
    output = format_search_results(results)
    assert "[production]" in output
    assert "[staging]" in output
    assert output.index("[production]") < output.index("[staging]")


def test_format_results_shows_values():
    results = [SearchResult("dev", "API_KEY", "mykey")]
    output = format_search_results(results, show_values=True)
    assert "API_KEY = mykey" in output


class Args:
    def __init__(self, **kwargs):
        defaults = {
            "vault": None,
            "password": "secret123",
            "key_pattern": None,
            "value_contains": None,
            "env": None,
            "show_values": False,
            "format": "text",
        }
        defaults.update(kwargs)
        self.__dict__.update(defaults)


def test_cmd_search_text_output(vault_file, capsys):
    from envault.cli_search import cmd_search

    cmd_search(Args(vault=vault_file, key_pattern="DB_*"))
    captured = capsys.readouterr()
    assert "DB_HOST" in captured.out


def test_cmd_search_json_output(vault_file, capsys):
    from envault.cli_search import cmd_search

    cmd_search(Args(vault=vault_file, key_pattern="API_KEY", format="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert all("key" in item for item in data)
