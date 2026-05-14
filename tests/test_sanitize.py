"""Tests for envault.sanitize and envault.cli_sanitize."""
from __future__ import annotations

import sys
import tempfile
import os
import pytest

from envault.sanitize import sanitize_secrets, SanitizeResult
from envault.vault import write_secrets, read_secrets
from envault.cli_sanitize import cmd_sanitize


# ---------------------------------------------------------------------------
# Unit tests for sanitize_secrets
# ---------------------------------------------------------------------------

def test_strips_whitespace_by_default():
    result = sanitize_secrets({"KEY": "  hello  "})
    assert result.cleaned["KEY"] == "hello"


def test_no_strip_preserves_whitespace():
    result = sanitize_secrets({"KEY": "  hello  "}, strip_whitespace=False)
    assert result.cleaned["KEY"] == "  hello  "


def test_strip_quotes_removes_double_quotes():
    result = sanitize_secrets({"KEY": '"value"'}, strip_quotes=True)
    assert result.cleaned["KEY"] == "value"


def test_strip_quotes_removes_single_quotes():
    result = sanitize_secrets({"KEY": "'value'"}, strip_quotes=True)
    assert result.cleaned["KEY"] == "value"


def test_strip_quotes_off_by_default():
    result = sanitize_secrets({"KEY": '"value"'})
    assert result.cleaned["KEY"] == '"value"'


def test_warns_on_placeholder_value():
    result = sanitize_secrets({"KEY": "CHANGE_ME"})
    assert any("placeholder" in w for w in result.warnings)


def test_warns_on_empty_value():
    result = sanitize_secrets({"KEY": ""})
    assert any("empty" in w for w in result.warnings)


def test_no_warn_placeholders_suppresses():
    result = sanitize_secrets({"KEY": "CHANGE_ME"}, warn_placeholders=False)
    assert not any("placeholder" in w for w in result.warnings)


def test_no_warn_empty_suppresses():
    result = sanitize_secrets({"KEY": ""}, warn_empty=False)
    assert not any("empty" in w for w in result.warnings)


def test_total_changed_counts_modifications():
    result = sanitize_secrets({"A": "  x  ", "B": "ok"})
    # 'A' was modified (whitespace stripped)
    assert result.total_changed >= 1


def test_clean_secrets_no_warnings():
    result = sanitize_secrets({"API_KEY": "abc123", "HOST": "localhost"})
    assert result.warnings == []
    assert result.cleaned == {"API_KEY": "abc123", "HOST": "localhost"}


# ---------------------------------------------------------------------------
# Integration test via cmd_sanitize
# ---------------------------------------------------------------------------

class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def vault_and_env(tmp_path):
    vault = str(tmp_path / "vault.json")
    pw = "testpass"
    write_secrets(vault, "dev", pw, {"KEY": "  hello  ", "PLACEHOLDER": "CHANGE_ME"})
    return vault, "dev", pw


def test_cmd_sanitize_writes_stripped_values(vault_and_env, capsys):
    vault, env, pw = vault_and_env
    args = Args(
        vault=vault, env=env, password=pw,
        dry_run=False, no_strip=False, strip_quotes=False,
        no_warn_placeholders=False, no_warn_empty=False,
    )
    cmd_sanitize(args)
    secrets = read_secrets(vault, env, pw)
    assert secrets["KEY"] == "hello"


def test_cmd_sanitize_dry_run_does_not_write(vault_and_env):
    vault, env, pw = vault_and_env
    args = Args(
        vault=vault, env=env, password=pw,
        dry_run=True, no_strip=False, strip_quotes=False,
        no_warn_placeholders=False, no_warn_empty=False,
    )
    with pytest.raises(SystemExit):
        cmd_sanitize(args)
    # Original value should be unchanged
    secrets = read_secrets(vault, env, pw)
    assert secrets["KEY"] == "  hello  "
