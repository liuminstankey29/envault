"""Tests for envault.cli_import CLI command."""

import io
import json
import sys
import tempfile
import os
import pytest

from envault.cli_import import cmd_import, register_import_parser
from envault.vault import write_secrets, read_secrets


class Args:
    def __init__(self, **kwargs):
        defaults = {
            "vault": None,
            "environment": "dev",
            "password": "secret",
            "file": None,
            "overwrite": False,
            "audit_log": None,
        }
        defaults.update(kwargs)
        self.__dict__.update(defaults)


@pytest.fixture()
def vault_and_src(tmp_path):
    vault = str(tmp_path / "vault.enc")
    src = tmp_path / "import.env"
    return vault, src


class TestCmdImport:
    def test_imports_secrets_and_prints_count(self, vault_and_src):
        vault, src = vault_and_src
        src.write_text("FOO=bar\nBAZ=qux")
        out = io.StringIO()
        cmd_import(Args(vault=vault, file=str(src)), out=out)
        output = out.getvalue()
        assert "2" in output
        assert "dev" in output

    def test_keys_listed_in_output(self, vault_and_src):
        vault, src = vault_and_src
        src.write_text("ALPHA=1\nBETA=2")
        out = io.StringIO()
        cmd_import(Args(vault=vault, file=str(src)), out=out)
        output = out.getvalue()
        assert "ALPHA" in output
        assert "BETA" in output

    def test_no_overwrite_message(self, vault_and_src):
        vault, src = vault_and_src
        write_secrets(vault, "dev", "secret", {"FOO": "existing"})
        src.write_text("FOO=new")
        out = io.StringIO()
        cmd_import(Args(vault=vault, file=str(src), overwrite=False), out=out)
        assert "No new secrets" in out.getvalue()

    def test_overwrite_flag_replaces_value(self, vault_and_src):
        vault, src = vault_and_src
        write_secrets(vault, "dev", "secret", {"FOO": "old"})
        src.write_text("FOO=new")
        out = io.StringIO()
        cmd_import(Args(vault=vault, file=str(src), overwrite=True), out=out)
        result = read_secrets(vault, "dev", "secret")
        assert result["FOO"] == "new"

    def test_missing_file_exits(self, tmp_path):
        vault = str(tmp_path / "vault.enc")
        with pytest.raises(SystemExit):
            cmd_import(Args(vault=vault, file=str(tmp_path / "nope.env")))

    def test_json_import(self, vault_and_src):
        vault, _ = vault_and_src
        src = _.parent / "data.json"
        src.write_text(json.dumps({"TOKEN": "xyz"}))
        out = io.StringIO()
        cmd_import(Args(vault=vault, file=str(src)), out=out)
        result = read_secrets(vault, "dev", "secret")
        assert result["TOKEN"] == "xyz"


class TestRegisterImportParser:
    def test_parser_registered(self):
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_import_parser(sub)
        args = parser.parse_args(["import", "prod", "file.env", "-p", "pw"])
        assert args.environment == "prod"
        assert args.password == "pw"
        assert args.overwrite is False

    def test_overwrite_flag(self):
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_import_parser(sub)
        args = parser.parse_args(["import", "dev", "f.env", "-p", "pw", "--overwrite"])
        assert args.overwrite is True
