"""Tests for envault.history."""
import json
import pytest
from pathlib import Path

from envault.history import (
    record_change,
    read_history,
    format_history,
    HistoryEntry,
)


@pytest.fixture
def vault_file(tmp_path):
    return str(tmp_path / "test.vault")


def test_record_change_creates_history_file(vault_file):
    record_change(vault_file, "prod", "DB_URL", "set")
    hist = Path(vault_file).parent / "test.history.json"
    assert hist.exists()


def test_record_change_returns_entry(vault_file):
    entry = record_change(vault_file, "prod", "API_KEY", "set", actor="alice")
    assert isinstance(entry, HistoryEntry)
    assert entry.environment == "prod"
    assert entry.key == "API_KEY"
    assert entry.action == "set"
    assert entry.actor == "alice"


def test_multiple_records_appended(vault_file):
    record_change(vault_file, "prod", "A", "set")
    record_change(vault_file, "prod", "B", "delete")
    entries = read_history(vault_file)
    assert len(entries) == 2


def test_read_history_empty_when_no_file(vault_file):
    entries = read_history(vault_file)
    assert entries == []


def test_filter_by_environment(vault_file):
    record_change(vault_file, "prod", "X", "set")
    record_change(vault_file, "staging", "X", "set")
    entries = read_history(vault_file, environment="prod")
    assert all(e.environment == "prod" for e in entries)
    assert len(entries) == 1


def test_filter_by_key(vault_file):
    record_change(vault_file, "prod", "KEY_A", "set")
    record_change(vault_file, "prod", "KEY_B", "set")
    entries = read_history(vault_file, key="KEY_A")
    assert len(entries) == 1
    assert entries[0].key == "KEY_A"


def test_filter_by_action(vault_file):
    record_change(vault_file, "prod", "A", "set")
    record_change(vault_file, "prod", "A", "rotate")
    entries = read_history(vault_file, action="rotate")
    assert len(entries) == 1
    assert entries[0].action == "rotate"


def test_limit_returns_last_n(vault_file):
    for i in range(5):
        record_change(vault_file, "prod", f"K{i}", "set")
    entries = read_history(vault_file, limit=2)
    assert len(entries) == 2
    assert entries[-1].key == "K4"


def test_format_history_contains_key(vault_file):
    record_change(vault_file, "prod", "SECRET_TOKEN", "set", actor="bob")
    entries = read_history(vault_file)
    output = format_history(entries)
    assert "SECRET_TOKEN" in output
    assert "bob" in output


def test_format_history_empty(vault_file):
    output = format_history([])
    assert "no history" in output
