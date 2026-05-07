"""Tests for envault.snapshot."""

from __future__ import annotations

import json
import pytest

from envault.vault import write_secrets
from envault.snapshot import (
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    write_secrets(path, "pw", "production", {"DB_URL": "postgres://prod", "TOKEN": "abc"})
    write_secrets(path, "pw", "staging", {"DB_URL": "postgres://staging"})
    return path


def test_create_snapshot_returns_name(vault_file):
    name = create_snapshot(vault_file, "pw", "production")
    assert "production" in name


def test_create_snapshot_custom_name(vault_file):
    name = create_snapshot(vault_file, "pw", "production", name="my_snap")
    assert name == "my_snap"


def test_snapshot_file_written(vault_file, tmp_path):
    create_snapshot(vault_file, "pw", "production", name="snap1")
    snap_path = tmp_path / ".envault_snapshots" / "snap1.json"
    assert snap_path.exists()
    data = json.loads(snap_path.read_text())
    assert data["environment"] == "production"
    assert data["secrets"]["DB_URL"] == "postgres://prod"


def test_restore_snapshot_recovers_secrets(vault_file):
    create_snapshot(vault_file, "pw", "production", name="snap_restore")
    # overwrite with new data
    write_secrets(vault_file, "pw", "production", {"DB_URL": "changed"})
    count = restore_snapshot(vault_file, "pw", "snap_restore")
    assert count == 2
    from envault.vault import read_secrets
    restored = read_secrets(vault_file, "pw", "production")
    assert restored["DB_URL"] == "postgres://prod"
    assert restored["TOKEN"] == "abc"


def test_restore_to_different_environment(vault_file):
    create_snapshot(vault_file, "pw", "production", name="snap_cross")
    count = restore_snapshot(vault_file, "pw", "snap_cross", environment="dr")
    assert count == 2
    from envault.vault import read_secrets
    secrets = read_secrets(vault_file, "pw", "dr")
    assert secrets["TOKEN"] == "abc"


def test_restore_missing_snapshot_raises(vault_file):
    with pytest.raises(FileNotFoundError, match="no_such"):
        restore_snapshot(vault_file, "pw", "no_such")


def test_list_snapshots_empty(vault_file):
    result = list_snapshots(vault_file)
    assert result == []


def test_list_snapshots_returns_metadata(vault_file):
    create_snapshot(vault_file, "pw", "production", name="s1")
    create_snapshot(vault_file, "pw", "staging", name="s2")
    result = list_snapshots(vault_file)
    names = [r["name"] for r in result]
    assert "s1" in names
    assert "s2" in names
    assert all("created_at" in r for r in result)
    assert all("key_count" in r for r in result)


def test_delete_snapshot_returns_true(vault_file):
    create_snapshot(vault_file, "pw", "production", name="del_me")
    assert delete_snapshot(vault_file, "del_me") is True
    assert list_snapshots(vault_file) == []


def test_delete_nonexistent_snapshot_returns_false(vault_file):
    assert delete_snapshot(vault_file, "ghost") is False
