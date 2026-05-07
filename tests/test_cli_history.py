"""Tests for envault.cli_history.cmd_history."""
import json
import pytest

from envault.history import record_change
from envault.cli_history import cmd_history


class Args:
    def __init__(self, vault, env=None, key=None, action=None, limit=None, fmt="text"):
        self.vault = vault
        self.env = env
        self.key = key
        self.action = action
        self.limit = limit
        self.format = fmt


@pytest.fixture
def vault_with_history(tmp_path):
    vf = str(tmp_path / "v.vault")
    record_change(vf, "prod", "DB_PASS", "set", actor="alice")
    record_change(vf, "staging", "API_KEY", "rotate")
    return vf


def test_cmd_history_text_output(vault_with_history, capsys):
    cmd_history(Args(vault=vault_with_history))
    out = capsys.readouterr().out
    assert "DB_PASS" in out
    assert "API_KEY" in out


def test_cmd_history_json_output(vault_with_history, capsys):
    cmd_history(Args(vault=vault_with_history, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 2


def test_cmd_history_filter_env(vault_with_history, capsys):
    cmd_history(Args(vault=vault_with_history, env="prod", fmt="json"))
    data = json.loads(capsys.readouterr().out)
    assert all(e["environment"] == "prod" for e in data)


def test_cmd_history_filter_action(vault_with_history, capsys):
    cmd_history(Args(vault=vault_with_history, action="rotate", fmt="json"))
    data = json.loads(capsys.readouterr().out)
    assert all(e["action"] == "rotate" for e in data)


def test_cmd_history_limit(vault_with_history, capsys):
    cmd_history(Args(vault=vault_with_history, limit=1, fmt="json"))
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 1


def test_cmd_history_no_file(tmp_path, capsys):
    vf = str(tmp_path / "empty.vault")
    cmd_history(Args(vault=vf))
    out = capsys.readouterr().out
    assert "no history" in out
