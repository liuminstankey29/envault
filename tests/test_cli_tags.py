"""Tests for envault.cli_tags module."""

from __future__ import annotations

import io
import sys
import pytest

from envault.vault import write_secrets
from envault.tags import add_tag
from envault.cli_tags import cmd_tags


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def vault_and_env(tmp_path):
    path = str(tmp_path / "vault.enc")
    pw = "pw123"
    write_secrets(path, "staging", pw, {"TOKEN": "abc", "SECRET": "xyz"})
    return path, pw


def test_cmd_tags_add(vault_and_env, capsys):
    path, pw = vault_and_env
    args = Args(vault=path, env="staging", password=pw,
                tags_command="add", key="TOKEN", tag="auth")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "auth" in out
    assert "TOKEN" in out


def test_cmd_tags_add_missing_key_exits(vault_and_env, capsys):
    path, pw = vault_and_env
    args = Args(vault=path, env="staging", password=pw,
                tags_command="add", key="NOPE", tag="auth")
    with pytest.raises(SystemExit) as exc_info:
        cmd_tags(args)
    assert exc_info.value.code == 1


def test_cmd_tags_list(vault_and_env, capsys):
    path, pw = vault_and_env
    add_tag(path, "staging", pw, "TOKEN", "auth")
    args = Args(vault=path, env="staging", password=pw,
                tags_command="list", key="TOKEN")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "auth" in out


def test_cmd_tags_list_empty(vault_and_env, capsys):
    path, pw = vault_and_env
    args = Args(vault=path, env="staging", password=pw,
                tags_command="list", key="TOKEN")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "No tags" in out


def test_cmd_tags_remove_present(vault_and_env, capsys):
    path, pw = vault_and_env
    add_tag(path, "staging", pw, "SECRET", "sensitive")
    args = Args(vault=path, env="staging", password=pw,
                tags_command="remove", key="SECRET", tag="sensitive")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "removed" in out


def test_cmd_tags_remove_absent(vault_and_env, capsys):
    path, pw = vault_and_env
    args = Args(vault=path, env="staging", password=pw,
                tags_command="remove", key="SECRET", tag="nothere")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "not present" in out


def test_cmd_tags_filter_masked(vault_and_env, capsys):
    path, pw = vault_and_env
    add_tag(path, "staging", pw, "TOKEN", "auth")
    args = Args(vault=path, env="staging", password=pw,
                tags_command="filter", tag="auth", reveal=False)
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "TOKEN" in out
    assert "***" in out
    assert "abc" not in out


def test_cmd_tags_filter_revealed(vault_and_env, capsys):
    path, pw = vault_and_env
    add_tag(path, "staging", pw, "TOKEN", "auth")
    args = Args(vault=path, env="staging", password=pw,
                tags_command="filter", tag="auth", reveal=True)
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "abc" in out
