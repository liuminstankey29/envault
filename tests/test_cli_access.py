"""Tests for envault.cli_access module."""
import sys
import pytest

from envault.access import AccessRule, set_access_rule
from envault.cli_access import cmd_access


class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def vault_and_env(tmp_path):
    vault = str(tmp_path / "v.env")
    return vault, "staging"


def test_cmd_access_set_prints_confirmation(vault_and_env, capsys):
    vault, env = vault_and_env
    args = Args(access_cmd="set", vault=vault, environment=env,
                role="dev", readable=["DB_URL"], writable=["APP_KEY"])
    cmd_access(args)
    out = capsys.readouterr().out
    assert "dev" in out
    assert "staging" in out


def test_cmd_access_set_empty_readable_shows_all(vault_and_env, capsys):
    vault, env = vault_and_env
    args = Args(access_cmd="set", vault=vault, environment=env,
                role="admin", readable=None, writable=None)
    cmd_access(args)
    out = capsys.readouterr().out
    assert "(all)" in out


def test_cmd_access_show_prints_rule(vault_and_env, capsys):
    vault, env = vault_and_env
    set_access_rule(vault, AccessRule("ops", env, ["KEY"], ["KEY"]))
    args = Args(access_cmd="show", vault=vault, environment=env, role="ops")
    cmd_access(args)
    out = capsys.readouterr().out
    assert "ops" in out
    assert "KEY" in out


def test_cmd_access_show_missing_rule_exits_1(vault_and_env):
    vault, env = vault_and_env
    args = Args(access_cmd="show", vault=vault, environment=env, role="ghost")
    with pytest.raises(SystemExit) as exc:
        cmd_access(args)
    assert exc.value.code == 1


def test_cmd_access_remove_existing_rule(vault_and_env, capsys):
    vault, env = vault_and_env
    set_access_rule(vault, AccessRule("viewer", env, [], []))
    args = Args(access_cmd="remove", vault=vault, environment=env, role="viewer")
    cmd_access(args)
    out = capsys.readouterr().out
    assert "Removed" in out


def test_cmd_access_remove_missing_rule_exits_1(vault_and_env):
    vault, env = vault_and_env
    args = Args(access_cmd="remove", vault=vault, environment=env, role="nobody")
    with pytest.raises(SystemExit) as exc:
        cmd_access(args)
    assert exc.value.code == 1


def test_cmd_access_list_shows_rules(vault_and_env, capsys):
    vault, env = vault_and_env
    set_access_rule(vault, AccessRule("r1", env, ["A"], ["B"]))
    args = Args(access_cmd="list", vault=vault, environment=None)
    cmd_access(args)
    out = capsys.readouterr().out
    assert "r1" in out


def test_cmd_access_check_allowed(vault_and_env, capsys):
    vault, env = vault_and_env
    set_access_rule(vault, AccessRule("dev", env, ["TOKEN"], []))
    args = Args(access_cmd="check", vault=vault, environment=env,
                role="dev", action="read", key="TOKEN")
    cmd_access(args)
    out = capsys.readouterr().out
    assert "ALLOWED" in out


def test_cmd_access_check_denied_exits_1(vault_and_env):
    vault, env = vault_and_env
    set_access_rule(vault, AccessRule("dev", env, ["TOKEN"], []))
    args = Args(access_cmd="check", vault=vault, environment=env,
                role="dev", action="write", key="TOKEN")
    with pytest.raises(SystemExit) as exc:
        cmd_access(args)
    assert exc.value.code == 1
