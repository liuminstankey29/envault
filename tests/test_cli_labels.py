"""Tests for envault.cli_labels."""
import pytest
from pathlib import Path
from io import StringIO
import sys

from envault.labels import add_label
from envault.cli_labels import cmd_labels


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def vault_and_env(tmp_path: Path):
    vault = str(tmp_path / "vault.env")
    return vault, "production"


def test_cmd_labels_add_new(vault_and_env, capsys):
    vault, env = vault_and_env
    args = Args(vault=vault, environment=env, labels_sub="add", key="DB_PASS", label="sensitive")
    cmd_labels(args)
    out = capsys.readouterr().out
    assert "added" in out
    assert "sensitive" in out


def test_cmd_labels_add_already_present(vault_and_env, capsys):
    vault, env = vault_and_env
    add_label(vault, env, "DB_PASS", "sensitive")
    args = Args(vault=vault, environment=env, labels_sub="add", key="DB_PASS", label="sensitive")
    cmd_labels(args)
    out = capsys.readouterr().out
    assert "already present" in out


def test_cmd_labels_remove_existing(vault_and_env, capsys):
    vault, env = vault_and_env
    add_label(vault, env, "TOKEN", "external")
    args = Args(vault=vault, environment=env, labels_sub="remove", key="TOKEN", label="external")
    cmd_labels(args)
    out = capsys.readouterr().out
    assert "removed" in out


def test_cmd_labels_remove_not_present(vault_and_env, capsys):
    vault, env = vault_and_env
    args = Args(vault=vault, environment=env, labels_sub="remove", key="TOKEN", label="ghost")
    cmd_labels(args)
    out = capsys.readouterr().out
    assert "not present" in out


def test_cmd_labels_list_shows_labels(vault_and_env, capsys):
    vault, env = vault_and_env
    add_label(vault, env, "API_KEY", "external")
    args = Args(vault=vault, environment=env, labels_sub="list", key=None)
    cmd_labels(args)
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "external" in out


def test_cmd_labels_list_empty(vault_and_env, capsys):
    vault, env = vault_and_env
    args = Args(vault=vault, environment=env, labels_sub="list", key=None)
    cmd_labels(args)
    out = capsys.readouterr().out
    assert "no labels" in out


def test_cmd_labels_filter_returns_keys(vault_and_env, capsys):
    vault, env = vault_and_env
    add_label(vault, env, "SECRET_A", "sensitive")
    add_label(vault, env, "SECRET_B", "sensitive")
    args = Args(vault=vault, environment=env, labels_sub="filter", label="sensitive")
    cmd_labels(args)
    out = capsys.readouterr().out
    assert "SECRET_A" in out
    assert "SECRET_B" in out


def test_cmd_labels_unknown_sub_exits(vault_and_env):
    vault, env = vault_and_env
    args = Args(vault=vault, environment=env, labels_sub="bogus")
    with pytest.raises(SystemExit) as exc_info:
        cmd_labels(args)
    assert exc_info.value.code == 1
