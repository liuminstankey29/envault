"""Tests for envault.cli_archive CLI commands."""

from __future__ import annotations

import sys
import pytest

from envault.vault import write_secrets, read_secrets
from envault.cli_archive import cmd_archive, cmd_restore


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def vault_and_env(tmp_path):
    vault = str(tmp_path / "vault.json")
    write_secrets(vault, "prod", "secret", {"KEY": "val1", "OTHER": "val2"})
    archive = str(tmp_path / "prod.tar.gz")
    return vault, archive, tmp_path


def test_cmd_archive_prints_summary(vault_and_env, capsys):
    vault, archive, _ = vault_and_env
    args = Args(vault=vault, environment="prod", password="secret", output=archive, label=None)
    cmd_archive(args)
    out = capsys.readouterr().out
    assert "prod" in out
    assert "2 keys" in out
    assert archive in out


def test_cmd_archive_default_output_name(vault_and_env, capsys, tmp_path, monkeypatch):
    vault, _, _ = vault_and_env
    monkeypatch.chdir(tmp_path)
    args = Args(vault=vault, environment="prod", password="secret", output=None, label=None)
    cmd_archive(args)
    out = capsys.readouterr().out
    assert "prod.envault.tar.gz" in out


def test_cmd_archive_bad_password_exits(vault_and_env, capsys):
    vault, archive, _ = vault_and_env
    args = Args(vault=vault, environment="prod", password="wrong", output=archive, label=None)
    with pytest.raises(SystemExit) as exc:
        cmd_archive(args)
    assert exc.value.code == 1


def test_cmd_restore_prints_summary(vault_and_env, capsys, tmp_path):
    vault, archive, _ = vault_and_env
    arc_args = Args(vault=vault, environment="prod", password="secret", output=archive, label=None)
    cmd_archive(arc_args)

    new_vault = str(tmp_path / "new.json")
    args = Args(vault=new_vault, archive=archive, password="secret", overwrite=False, environment=None)
    cmd_restore(args)
    out = capsys.readouterr().out
    assert "2" in out
    assert "prod" in out


def test_cmd_restore_shows_skipped(vault_and_env, capsys, tmp_path):
    vault, archive, _ = vault_and_env
    arc_args = Args(vault=vault, environment="prod", password="secret", output=archive, label=None)
    cmd_archive(arc_args)

    # prod already has KEY and OTHER, restoring again without overwrite should skip both
    args = Args(vault=vault, archive=archive, password="secret", overwrite=False, environment="prod")
    cmd_restore(args)
    out = capsys.readouterr().out
    assert "skipped 2" in out


def test_cmd_restore_bad_archive_exits(vault_and_env, capsys, tmp_path):
    vault, _, _ = vault_and_env
    args = Args(
        vault=vault,
        archive=str(tmp_path / "nonexistent.tar.gz"),
        password="secret",
        overwrite=False,
        environment=None,
    )
    with pytest.raises(SystemExit) as exc:
        cmd_restore(args)
    assert exc.value.code == 1
