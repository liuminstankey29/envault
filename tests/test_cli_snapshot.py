"""Tests for envault.cli_snapshot."""

from __future__ import annotations

import json
import pytest

from envault.vault import write_secrets, read_secrets
from envault.snapshot import create_snapshot
from envault.cli_snapshot import cmd_snapshot


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def vault_and_env(tmp_path):
    path = str(tmp_path / "vault.enc")
    write_secrets(path, "secret", "prod", {"KEY": "val1", "OTHER": "val2"})
    return path


def test_cmd_snapshot_create(vault_and_env, capsys):
    args = Args(vault=vault_and_env, password="secret", environment="prod",
                name="snap_test", snapshot_cmd="create")
    cmd_snapshot(args)
    out = capsys.readouterr().out
    assert "snap_test" in out
    assert "prod" in out


def test_cmd_snapshot_list_table(vault_and_env, capsys):
    create_snapshot(vault_and_env, "secret", "prod", name="listed")
    args = Args(vault=vault_and_env, password="secret", snapshot_cmd="list", json=False)
    cmd_snapshot(args)
    out = capsys.readouterr().out
    assert "listed" in out
    assert "prod" in out


def test_cmd_snapshot_list_json(vault_and_env, capsys):
    create_snapshot(vault_and_env, "secret", "prod", name="json_snap")
    args = Args(vault=vault_and_env, password="secret", snapshot_cmd="list", json=True)
    cmd_snapshot(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert any(s["name"] == "json_snap" for s in data)


def test_cmd_snapshot_list_empty(vault_and_env, capsys):
    args = Args(vault=vault_and_env, password="secret", snapshot_cmd="list", json=False)
    cmd_snapshot(args)
    out = capsys.readouterr().out
    assert "No snapshots" in out


def test_cmd_snapshot_restore(vault_and_env, capsys):
    create_snapshot(vault_and_env, "secret", "prod", name="restore_snap")
    write_secrets(vault_and_env, "secret", "prod", {"KEY": "overwritten"})
    args = Args(vault=vault_and_env, password="secret", snapshot_cmd="restore",
                name="restore_snap", target_environment=None)
    cmd_snapshot(args)
    out = capsys.readouterr().out
    assert "Restored" in out
    secrets = read_secrets(vault_and_env, "secret", "prod")
    assert secrets["KEY"] == "val1"


def test_cmd_snapshot_delete(vault_and_env, capsys):
    create_snapshot(vault_and_env, "secret", "prod", name="bye")
    args = Args(vault=vault_and_env, password="secret", snapshot_cmd="delete", name="bye")
    cmd_snapshot(args)
    out = capsys.readouterr().out
    assert "deleted" in out


def test_cmd_snapshot_delete_missing_exits(vault_and_env):
    args = Args(vault=vault_and_env, password="secret", snapshot_cmd="delete", name="nope")
    with pytest.raises(SystemExit) as exc_info:
        cmd_snapshot(args)
    assert exc_info.value.code == 1
