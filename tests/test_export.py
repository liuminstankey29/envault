"""Tests for envault.export formatting helpers."""

from __future__ import annotations

import json
import pytest

from envault.export import (
    export_secrets,
    format_dotenv,
    format_shell,
    format_json,
)

SAMPLE = {"DB_PASS": "s3cr3t", "API_KEY": "abc123", "QUOTE": 'say "hi"'}


class TestFormatDotenv:
    def test_output_contains_all_keys(self):
        out = format_dotenv(SAMPLE)
        for key in SAMPLE:
            assert key in out

    def test_values_quoted(self):
        out = format_dotenv({"FOO": "bar"})
        assert 'FOO="bar"' in out

    def test_double_quotes_escaped(self):
        out = format_dotenv({"X": 'say "hi"'})
        assert 'say \\"hi\\"' in out

    def test_empty_dict_returns_empty_string(self):
        assert format_dotenv({}) == ""

    def test_trailing_newline(self):
        out = format_dotenv({"A": "1"})
        assert out.endswith("\n")


class TestFormatShell:
    def test_export_prefix(self):
        out = format_shell({"FOO": "bar"})
        assert out.startswith("export ")

    def test_all_keys_exported(self):
        out = format_shell(SAMPLE)
        for key in SAMPLE:
            assert f"export {key}=" in out


class TestFormatJson:
    def test_valid_json(self):
        out = format_json(SAMPLE)
        parsed = json.loads(out)
        assert parsed == SAMPLE

    def test_sorted_keys(self):
        out = format_json({"Z": "1", "A": "2"})
        parsed = json.loads(out)
        assert list(parsed.keys()) == sorted(parsed.keys())


class TestExportSecrets:
    def test_default_format_is_dotenv(self):
        out = export_secrets({"K": "v"})
        assert 'K="v"' in out

    def test_json_format(self):
        out = export_secrets({"K": "v"}, fmt="json")
        assert json.loads(out) == {"K": "v"}

    def test_unknown_format_raises(self):
        with pytest.raises(ValueError, match="Unknown format"):
            export_secrets({"K": "v"}, fmt="yaml")  # type: ignore[arg-type]
