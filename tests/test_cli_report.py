"""Tests for envault.cli_report module."""
from __future__ import annotations

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

from envault.vault import write_secrets
from envault.cli_report import cmd_report


class Args:
    def __init__(self, vault, password, environment=None, format="text"):
        self.vault = str(vault)
        self.password = password
        self.environment = environment
        self.format = format


@pytest.fixture
def vault_and_env(tmp_path):
    vault = tmp_path / "vault.env"
    write_secrets(vault, "prod", "pw", {"KEY": "val", "OTHER": "x"})
    write_secrets(vault, "dev", "pw", {"KEY": "devval"})
    return vault


def test_cmd_report_text_output(vault_and_env, capsys):
    args = Args(vault_and_env, "pw", environment="prod")
    cmd_report(args)
    out = capsys.readouterr().out
    assert "prod" in out
    assert "2" in out


def test_cmd_report_json_output(vault_and_env, capsys):
    args = Args(vault_and_env, "pw", environment="prod", format="json")
    cmd_report(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["environment"] == "prod"
    assert data[0]["secret_count"] == 2


def test_cmd_report_all_environments(vault_and_env, capsys):
    args = Args(vault_and_env, "pw")
    cmd_report(args)
    out = capsys.readouterr().out
    assert "prod" in out
    assert "dev" in out


def test_cmd_report_exits_2_on_lint_errors(tmp_path, capsys):
    vault = tmp_path / "vault.env"
    write_secrets(vault, "prod", "pw", {"EMPTY": ""})
    args = Args(vault, "pw", environment="prod")
    with pytest.raises(SystemExit) as exc:
        cmd_report(args)
    assert exc.value.code == 2


def test_cmd_report_json_includes_locked_field(vault_and_env, capsys):
    from envault.lock import lock_environment
    lock_environment(vault_and_env, "prod")
    args = Args(vault_and_env, "pw", environment="prod", format="json")
    cmd_report(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data[0]["locked"] is True
