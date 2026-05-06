"""Tests for envault.import_env module."""

import json
import os
import tempfile
import pytest

from envault.import_env import parse_dotenv, parse_json_env, load_import_file, import_secrets


# ---------------------------------------------------------------------------
# parse_dotenv
# ---------------------------------------------------------------------------

class TestParseDotenv:
    def test_basic_key_value(self):
        result = parse_dotenv("FOO=bar")
        assert result == {"FOO": "bar"}

    def test_ignores_comments(self):
        result = parse_dotenv("# comment\nKEY=value")
        assert "KEY" in result
        assert len(result) == 1

    def test_ignores_blank_lines(self):
        result = parse_dotenv("\n\nKEY=value\n\n")
        assert result == {"KEY": "value"}

    def test_double_quoted_value(self):
        result = parse_dotenv('KEY="hello world"')
        assert result["KEY"] == "hello world"

    def test_single_quoted_value(self):
        result = parse_dotenv("KEY='hello world'")
        assert result["KEY"] == "hello world"

    def test_multiple_keys(self):
        result = parse_dotenv("A=1\nB=2\nC=3")
        assert result == {"A": "1", "B": "2", "C": "3"}

    def test_empty_value(self):
        result = parse_dotenv("EMPTY=")
        assert result["EMPTY"] == ""

    def test_invalid_line_skipped(self):
        result = parse_dotenv("not-valid\nGOOD=yes")
        assert result == {"GOOD": "yes"}


# ---------------------------------------------------------------------------
# parse_json_env
# ---------------------------------------------------------------------------

class TestParseJsonEnv:
    def test_basic(self):
        result = parse_json_env(json.dumps({"KEY": "value"}))
        assert result == {"KEY": "value"}

    def test_values_coerced_to_str(self):
        result = parse_json_env(json.dumps({"PORT": 8080}))
        assert result["PORT"] == "8080"

    def test_non_dict_raises(self):
        with pytest.raises(ValueError):
            parse_json_env(json.dumps(["a", "b"]))


# ---------------------------------------------------------------------------
# load_import_file
# ---------------------------------------------------------------------------

class TestLoadImportFile:
    def test_dotenv_file(self, tmp_path):
        f = tmp_path / "secrets.env"
        f.write_text("DB=postgres\nPORT=5432")
        result, fmt = load_import_file(str(f))
        assert fmt == "dotenv"
        assert result["DB"] == "postgres"

    def test_json_file(self, tmp_path):
        f = tmp_path / "secrets.json"
        f.write_text(json.dumps({"TOKEN": "abc"}))
        result, fmt = load_import_file(str(f))
        assert fmt == "json"
        assert result["TOKEN"] == "abc"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_import_file(str(tmp_path / "nope.env"))


# ---------------------------------------------------------------------------
# import_secrets integration
# ---------------------------------------------------------------------------

class TestImportSecrets:
    def test_imports_new_keys(self, tmp_path):
        vault = str(tmp_path / "vault.enc")
        src = tmp_path / "src.env"
        src.write_text("KEY=value")
        written = import_secrets(vault, "dev", "pass", str(src))
        assert written == {"KEY": "value"}

    def test_no_overwrite_by_default(self, tmp_path):
        from envault.vault import write_secrets
        vault = str(tmp_path / "vault.enc")
        write_secrets(vault, "dev", "pass", {"KEY": "original"})
        src = tmp_path / "src.env"
        src.write_text("KEY=new")
        written = import_secrets(vault, "dev", "pass", str(src), overwrite=False)
        assert written == {}

    def test_overwrite_replaces_key(self, tmp_path):
        from envault.vault import write_secrets, read_secrets
        vault = str(tmp_path / "vault.enc")
        write_secrets(vault, "dev", "pass", {"KEY": "original"})
        src = tmp_path / "src.env"
        src.write_text("KEY=new")
        import_secrets(vault, "dev", "pass", str(src), overwrite=True)
        result = read_secrets(vault, "dev", "pass")
        assert result["KEY"] == "new"
