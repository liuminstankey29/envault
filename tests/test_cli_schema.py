"""Tests for envault.cli_schema — cmd_schema."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

from envault.vault import write_secrets
from envault.cli_schema import cmd_schema


class Args:
    def __init__(self, vault, env, schema, password, fmt="text"):
        self.vault = vault
        self.env = env
        self.schema = schema
        self.password = password
        self.format = fmt


@pytest.fixture()
def vault_and_schema(tmp_path):
    vault = str(tmp_path / "vault.json")
    write_secrets(vault, "prod", "pass", {"DB_URL": "postgres://localhost/db", "PORT": "5432"})
    schema = tmp_path / "schema.json"
    schema.write_text(
        json.dumps([
            {"key": "DB_URL", "required": True},
            {"key": "PORT", "required": True, "pattern": "\\d+"},
        ])
    )
    return vault, str(schema)


def test_cmd_schema_passes_on_valid(vault_and_schema, capsys):
    vault, schema = vault_and_schema
    args = Args(vault, "prod", schema, "pass")
    cmd_schema(args)  # should not raise
    out = capsys.readouterr().out
    assert "passed" in out.lower()


def test_cmd_schema_exits_2_on_error(tmp_path):
    vault = str(tmp_path / "vault.json")
    write_secrets(vault, "prod", "pass", {"PORT": "abc"})
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps([{"key": "PORT", "pattern": "\\d+"}]))
    args = Args(vault, "prod", str(schema), "pass")
    with pytest.raises(SystemExit) as exc_info:
        cmd_schema(args)
    assert exc_info.value.code == 2


def test_cmd_schema_json_format(vault_and_schema, capsys):
    vault, schema = vault_and_schema
    args = Args(vault, "prod", schema, "pass", fmt="json")
    cmd_schema(args)
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert isinstance(parsed, list)


def test_cmd_schema_json_format_with_error(tmp_path, capsys):
    vault = str(tmp_path / "vault.json")
    write_secrets(vault, "prod", "pass", {})
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps([{"key": "MISSING", "required": True}]))
    args = Args(vault, "prod", str(schema), "pass", fmt="json")
    with pytest.raises(SystemExit):
        cmd_schema(args)
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert any(item["key"] == "MISSING" for item in parsed)


def test_cmd_schema_bad_password_exits(vault_and_schema):
    vault, schema = vault_and_schema
    args = Args(vault, "prod", schema, "wrongpass")
    with pytest.raises(SystemExit) as exc_info:
        cmd_schema(args)
    assert exc_info.value.code == 1
