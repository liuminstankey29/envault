"""Tests for envault.rename and envault.cli_rename."""

import io
import sys
import pytest
from envault.vault import write_secrets, read_secrets
from envault.rename import rename_secret, rename_secret_across_environments
from envault.cli_rename import cmd_rename


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.json")
    write_secrets(path, "prod", "pass1", {"DB_HOST": "localhost", "DB_PORT": "5432"})
    write_secrets(path, "staging", "pass1", {"DB_HOST": "staging-host", "API_KEY": "abc"})
    return path


def test_rename_changes_key(vault_file):
    rename_secret(vault_file, "prod", "DB_HOST", "DATABASE_HOST", "pass1")
    secrets = read_secrets(vault_file, "prod", "pass1")
    assert "DATABASE_HOST" in secrets
    assert "DB_HOST" not in secrets
    assert secrets["DATABASE_HOST"] == "localhost"


def test_rename_preserves_other_keys(vault_file):
    rename_secret(vault_file, "prod", "DB_HOST", "DATABASE_HOST", "pass1")
    secrets = read_secrets(vault_file, "prod", "pass1")
    assert secrets["DB_PORT"] == "5432"


def test_rename_missing_key_raises(vault_file):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        rename_secret(vault_file, "prod", "MISSING_KEY", "NEW_KEY", "pass1")


def test_rename_no_overwrite_skips(vault_file):
    result = rename_secret(vault_file, "prod", "DB_HOST", "DB_PORT", "pass1", overwrite=False)
    assert result["skipped"] is True
    assert result["renamed"] is False
    secrets = read_secrets(vault_file, "prod", "pass1")
    assert secrets["DB_PORT"] == "5432"  # unchanged


def test_rename_with_overwrite(vault_file):
    result = rename_secret(vault_file, "prod", "DB_HOST", "DB_PORT", "pass1", overwrite=True)
    assert result["renamed"] is True
    secrets = read_secrets(vault_file, "prod", "pass1")
    assert secrets["DB_PORT"] == "localhost"


def test_rename_across_environments(vault_file):
    results = rename_secret_across_environments(vault_file, "DB_HOST", "DATABASE_HOST", "pass1")
    envs_touched = {r["env"] for r in results}
    assert envs_touched == {"prod", "staging"}
    for env in ("prod", "staging"):
        s = read_secrets(vault_file, env, "pass1")
        assert "DATABASE_HOST" in s
        assert "DB_HOST" not in s


def test_rename_across_environments_skips_missing(vault_file):
    # API_KEY only in staging
    results = rename_secret_across_environments(vault_file, "API_KEY", "API_TOKEN", "pass1")
    assert len(results) == 1
    assert results[0]["env"] == "staging"


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_cmd_rename_prints_renamed(vault_file, capsys):
    args = Args(
        vault=vault_file, env="prod", old_key="DB_HOST",
        new_key="DATABASE_HOST", password="pass1",
        overwrite=False, all_envs=False,
    )
    cmd_rename(args)
    out = capsys.readouterr().out
    assert "RENAMED" in out
    assert "DB_HOST" in out
    assert "DATABASE_HOST" in out


def test_cmd_rename_prints_skipped(vault_file, capsys):
    args = Args(
        vault=vault_file, env="prod", old_key="DB_HOST",
        new_key="DB_PORT", password="pass1",
        overwrite=False, all_envs=False,
    )
    cmd_rename(args)
    out = capsys.readouterr().out
    assert "SKIPPED" in out


def test_cmd_rename_missing_key_exits(vault_file):
    args = Args(
        vault=vault_file, env="prod", old_key="NO_SUCH",
        new_key="X", password="pass1",
        overwrite=False, all_envs=False,
    )
    with pytest.raises(SystemExit) as exc_info:
        cmd_rename(args)
    assert exc_info.value.code == 1
