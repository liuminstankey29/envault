"""Tests for envault.cli_namespace."""
from __future__ import annotations

import io
import sys
import pytest

from envault.vault import write_secrets
from envault.namespace import assign_namespace
from envault.cli_namespace import cmd_namespace


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def vault_and_env(tmp_path):
    p = tmp_path / "vault.enc"
    write_secrets(str(p), "dev", "pass", {"DB_URL": "postgres://", "API_KEY": "key"})
    return str(p)


def test_cmd_namespace_assign_prints_count(vault_and_env, capsys):
    args = Args(
        vault=vault_and_env,
        namespace_cmd="assign",
        env="dev",
        password="pass",
        namespace="database",
        keys=["DB_URL"],
        overwrite=False,
    )
    cmd_namespace(args)
    out = capsys.readouterr().out
    assert "assigned 1 key" in out
    assert "database" in out


def test_cmd_namespace_assign_shows_skipped(vault_and_env, capsys):
    assign_namespace(vault_and_env, "dev", "pass", "ns1", ["API_KEY"])
    args = Args(
        vault=vault_and_env,
        namespace_cmd="assign",
        env="dev",
        password="pass",
        namespace="ns2",
        keys=["API_KEY"],
        overwrite=False,
    )
    cmd_namespace(args)
    out = capsys.readouterr().out
    assert "Skipped" in out
    assert "API_KEY" in out


def test_cmd_namespace_get_prints_namespace(vault_and_env, capsys):
    assign_namespace(vault_and_env, "dev", "pass", "auth", ["API_KEY"])
    args = Args(vault=vault_and_env, namespace_cmd="get", env="dev", key="API_KEY")
    cmd_namespace(args)
    out = capsys.readouterr().out
    assert "auth" in out


def test_cmd_namespace_get_unassigned_prints_message(vault_and_env, capsys):
    args = Args(vault=vault_and_env, namespace_cmd="get", env="dev", key="DB_URL")
    cmd_namespace(args)
    out = capsys.readouterr().out
    assert "no namespace" in out


def test_cmd_namespace_list_prints_keys(vault_and_env, capsys):
    assign_namespace(vault_and_env, "dev", "pass", "database", ["DB_URL"])
    args = Args(
        vault=vault_and_env,
        namespace_cmd="list",
        env="dev",
        password="pass",
        namespace="database",
    )
    cmd_namespace(args)
    out = capsys.readouterr().out
    assert "DB_URL" in out


def test_cmd_namespace_remove_prints_cleared(vault_and_env, capsys):
    assign_namespace(vault_and_env, "dev", "pass", "database", ["DB_URL"])
    args = Args(
        vault=vault_and_env,
        namespace_cmd="remove",
        env="dev",
        keys=["DB_URL"],
    )
    cmd_namespace(args)
    out = capsys.readouterr().out
    assert "1 key" in out


def test_cmd_namespace_unknown_subcommand_exits(vault_and_env):
    args = Args(vault=vault_and_env, namespace_cmd="bogus")
    with pytest.raises(SystemExit) as exc:
        cmd_namespace(args)
    assert exc.value.code == 1
