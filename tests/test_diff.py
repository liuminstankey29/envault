"""Tests for envault.diff module."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from envault.diff import (
    DiffEntry,
    diff_dicts,
    diff_environments,
    format_diff,
)
from envault.vault import write_secrets


# ---------------------------------------------------------------------------
# diff_dicts
# ---------------------------------------------------------------------------

class TestDiffDicts:
    def test_added_key(self):
        entries = diff_dicts({}, {"KEY": "val"})
        assert len(entries) == 1
        assert entries[0].status == "added"
        assert entries[0].key == "KEY"
        assert entries[0].new_value == "val"

    def test_removed_key(self):
        entries = diff_dicts({"KEY": "val"}, {})
        assert len(entries) == 1
        assert entries[0].status == "removed"
        assert entries[0].old_value == "val"

    def test_changed_key(self):
        entries = diff_dicts({"KEY": "old"}, {"KEY": "new"})
        assert len(entries) == 1
        assert entries[0].status == "changed"
        assert entries[0].old_value == "old"
        assert entries[0].new_value == "new"

    def test_unchanged_hidden_by_default(self):
        entries = diff_dicts({"KEY": "same"}, {"KEY": "same"})
        assert entries == []

    def test_unchanged_shown_when_requested(self):
        entries = diff_dicts({"KEY": "same"}, {"KEY": "same"}, show_unchanged=True)
        assert len(entries) == 1
        assert entries[0].status == "unchanged"

    def test_results_sorted_by_key(self):
        old = {"Z": "1", "A": "1"}
        new = {"Z": "2", "A": "1", "M": "3"}
        entries = diff_dicts(old, new)
        keys = [e.key for e in entries]
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# format_diff
# ---------------------------------------------------------------------------

class TestFormatDiff:
    def test_empty_returns_placeholder(self):
        assert format_diff([]) == "(no differences)"

    def test_masks_values_by_default(self):
        entries = [DiffEntry(key="SECRET", status="added", new_value="s3cr3t")]
        output = format_diff(entries)
        assert "s3cr3t" not in output
        assert "***" in output

    def test_reveal_shows_values(self):
        entries = [DiffEntry(key="SECRET", status="added", new_value="s3cr3t")]
        output = format_diff(entries, mask_values=False)
        assert "s3cr3t" in output

    def test_symbols_present(self):
        entries = [
            DiffEntry(key="A", status="added", new_value="1"),
            DiffEntry(key="B", status="removed", old_value="2"),
            DiffEntry(key="C", status="changed", old_value="3", new_value="4"),
        ]
        output = format_diff(entries)
        assert output.count("+") >= 1
        assert output.count("-") >= 1
        assert output.count("~") >= 1


# ---------------------------------------------------------------------------
# diff_environments (integration)
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.json")
    write_secrets(path, "staging", "pass1", {"DB": "staging-db", "SHARED": "same"})
    write_secrets(path, "prod", "pass2", {"DB": "prod-db", "SHARED": "same", "EXTRA": "only-prod"})
    return path


def test_diff_environments_detects_changes(vault_file):
    entries = diff_environments(vault_file, "staging", "pass1", "prod", "pass2")
    statuses = {e.key: e.status for e in entries}
    assert statuses["DB"] == "changed"
    assert statuses["EXTRA"] == "added"
    assert "SHARED" not in statuses  # unchanged, hidden by default


def test_diff_environments_show_unchanged(vault_file):
    entries = diff_environments(
        vault_file, "staging", "pass1", "prod", "pass2", show_unchanged=True
    )
    statuses = {e.key: e.status for e in entries}
    assert statuses["SHARED"] == "unchanged"
