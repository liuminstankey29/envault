"""Tests for envault.cli_promote."""
import pytest
from pathlib import Path
from envault.vault import write_secrets, read_secrets
from envault.cli_promote import cmd_promote, register_promote_parser
import argparse


class Args:
    def __init__(self, vault, src_env, dst_env, src_password, dst_password, keys=None, overwrite=False):
        self.vault = vault
        self.src_env = src_env
        self.dst_env = dst_env
        self.src_password = src_password
        self.dst_password = dst_password
        self.keys = keys or []
        self.overwrite = overwrite


@pytest.fixture
def vault_and_envs(tmp_path):
    vault = str(tmp_path / "vault.json")
    write_secrets(vault, "staging", "stagepw", {"KEY1": "val1", "KEY2": "val2"})
    write_secrets(vault, "production", "prodpw", {})
    return vault


def test_cmd_promote_prints_promoted(vault_and_envs, capsys):
    args = Args(vault_and_envs, "staging", "production", "stagepw", "prodpw")
    cmd_promote(args)
    out = capsys.readouterr().out
    assert "Promoted" in out
    assert "2" in out


def test_cmd_promote_skipped_shown(vault_and_envs, capsys):
    write_secrets(vault_and_envs, "production", "prodpw", {"KEY1": "existing"})
    args = Args(vault_and_envs, "staging", "production", "stagepw", "prodpw")
    cmd_promote(args)
    out = capsys.readouterr().out
    assert "Skipped" in out
    assert "KEY1" in out


def test_cmd_promote_overwrite_shown(vault_and_envs, capsys):
    write_secrets(vault_and_envs, "production", "prodpw", {"KEY1": "old"})
    args = Args(vault_and_envs, "staging", "production", "stagepw", "prodpw", overwrite=True)
    cmd_promote(args)
    out = capsys.readouterr().out
    assert "Overwrote" in out


def test_cmd_promote_missing_key_exits(vault_and_envs, capsys):
    args = Args(vault_and_envs, "staging", "production", "stagepw", "prodpw", keys=["NONEXISTENT"])
    with pytest.raises(SystemExit) as exc_info:
        cmd_promote(args)
    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "Error" in out


def test_register_promote_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_promote_parser(sub)
    args = parser.parse_args([
        "promote", "vault.json", "staging", "production",
        "--src-password", "sp", "--dst-password", "dp", "--overwrite"
    ])
    assert args.src_env == "staging"
    assert args.dst_env == "production"
    assert args.overwrite is True
