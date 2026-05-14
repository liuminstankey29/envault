"""Tests for envault.cli_rollback."""

from __future__ import annotations

import sys
import pytest
from pathlib import Path
from unittest.mock import patch

from envault.vault import write_secrets
from envault.snapshot import create_snapshot
from envault.cli_rollback import cmd_rollback


class Args:
    def __init__(self, **kwargs: object) -> None:
        self.vault: str = ""
        self.environment: str = ""
        self.password: str = ""
        self.snapshot: str | None = None
        self.steps: int | None = None
        self.list_snapshots: bool = False
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture()
def vault_and_env(tmp_path: Path):
    vault = tmp_path / "vault.json"
    write_secrets(vault, "staging", "pw", {"FOO": "bar", "BAZ": "qux"})
    snap = create_snapshot(vault, "staging", "pw")
    return vault, snap


def test_cmd_rollback_to_snapshot_prints_summary(vault_and_env, capsys):
    vault, snap = vault_and_env
    args = Args(
        vault=str(vault),
        environment="staging",
        password="pw",
        snapshot=snap,
    )
    cmd_rollback(args)
    out = capsys.readouterr().out
    assert "staging" in out
    assert snap in out
    assert "restored" in out


def test_cmd_rollback_bad_snapshot_exits_1(vault_and_env, capsys):
    vault, _ = vault_and_env
    args = Args(
        vault=str(vault),
        environment="staging",
        password="pw",
        snapshot="no-such-snap",
    )
    with pytest.raises(SystemExit) as exc_info:
        cmd_rollback(args)
    assert exc_info.value.code == 1


def test_cmd_rollback_list_snapshots_prints_names(vault_and_env, capsys):
    vault, snap = vault_and_env
    args = Args(
        vault=str(vault),
        environment="staging",
        password="pw",
        list_snapshots=True,
    )
    cmd_rollback(args)
    out = capsys.readouterr().out
    assert snap in out


def test_cmd_rollback_no_args_exits_1(vault_and_env, capsys):
    vault, _ = vault_and_env
    args = Args(
        vault=str(vault),
        environment="staging",
        password="pw",
    )
    with pytest.raises(SystemExit) as exc_info:
        cmd_rollback(args)
    assert exc_info.value.code == 1
