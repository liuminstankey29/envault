"""Tests for envault.rollback."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import write_secrets, read_secrets
from envault.snapshot import create_snapshot
from envault.rollback import rollback_to_snapshot, rollback_to_history


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    return tmp_path / "vault.json"


PASSWORD = "testpass"
ENV = "production"


def test_rollback_to_snapshot_restores_secrets(vault_file: Path) -> None:
    write_secrets(vault_file, ENV, PASSWORD, {"A": "1", "B": "2"})
    snap_name = create_snapshot(vault_file, ENV, PASSWORD)

    # Overwrite with new data
    write_secrets(vault_file, ENV, PASSWORD, {"A": "99", "C": "3"})

    result = rollback_to_snapshot(vault_file, ENV, PASSWORD, snap_name)

    assert result.source == "snapshot"
    assert result.label == snap_name
    assert result.keys_restored == 2
    assert result.previous_keys == 2

    restored = read_secrets(vault_file, ENV, PASSWORD)
    assert restored == {"A": "1", "B": "2"}


def test_rollback_to_snapshot_bad_name_raises(vault_file: Path) -> None:
    write_secrets(vault_file, ENV, PASSWORD, {"X": "1"})
    with pytest.raises((FileNotFoundError, KeyError)):
        rollback_to_snapshot(vault_file, ENV, PASSWORD, "nonexistent-snap")


def test_rollback_to_snapshot_records_history(vault_file: Path) -> None:
    from envault.history import read_history

    write_secrets(vault_file, ENV, PASSWORD, {"K": "v"})
    snap = create_snapshot(vault_file, ENV, PASSWORD)
    rollback_to_snapshot(vault_file, ENV, PASSWORD, snap)

    history = read_history(vault_file, environment=ENV)
    actions = [e.action for e in history]
    assert "rollback" in actions


def test_rollback_to_history_no_history_returns_none(vault_file: Path) -> None:
    write_secrets(vault_file, ENV, PASSWORD, {"A": "1"})
    result = rollback_to_history(vault_file, ENV, PASSWORD, steps=1)
    assert result is None


def test_rollback_to_history_result_fields(vault_file: Path) -> None:
    from envault.history import record_change

    write_secrets(vault_file, ENV, PASSWORD, {"A": "original"})
    # Simulate a history entry
    record_change(vault_file, environment=ENV, action="set", key="A", detail="original")

    write_secrets(vault_file, ENV, PASSWORD, {"A": "modified"})
    record_change(vault_file, environment=ENV, action="set", key="A", detail="modified")

    result = rollback_to_history(vault_file, ENV, PASSWORD, steps=1)
    assert result is not None
    assert result.source == "history"
    assert result.environment == ENV
