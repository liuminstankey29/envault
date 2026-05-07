"""Tests for envault.template and envault.cli_template."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from envault.template import render_template, render_template_file
from envault.vault import write_secrets


# ---------------------------------------------------------------------------
# render_template unit tests
# ---------------------------------------------------------------------------

def test_simple_substitution():
    result = render_template("Hello {{ NAME }}!", {"NAME": "World"})
    assert result == "Hello World!"


def test_multiple_placeholders():
    tmpl = "host={{ DB_HOST }} port={{ DB_PORT }}"
    result = render_template(tmpl, {"DB_HOST": "localhost", "DB_PORT": "5432"})
    assert result == "host=localhost port=5432"


def test_placeholder_with_spaces():
    result = render_template("{{  KEY  }}", {"KEY": "value"})
    assert result == "value"


def test_strict_raises_on_missing_key():
    with pytest.raises(KeyError, match="MISSING"):
        render_template("{{ MISSING }}", {}, strict=True)


def test_loose_leaves_unknown_placeholder():
    result = render_template("{{ MISSING }}", {}, strict=False)
    assert result == "{{ MISSING }}"


def test_no_placeholders_unchanged():
    tmpl = "nothing to replace"
    assert render_template(tmpl, {"X": "y"}) == tmpl


def test_repeated_placeholder():
    result = render_template("{{ A }}-{{ A }}", {"A": "x"})
    assert result == "x-x"


# ---------------------------------------------------------------------------
# render_template_file integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_and_template(tmp_path: Path):
    vault = tmp_path / "vault.enc"
    write_secrets(str(vault), "prod", "secret", {"HOST": "db.example.com", "PORT": "5432"})
    tmpl = tmp_path / "config.tmpl"
    tmpl.write_text("host={{ HOST }}\nport={{ PORT }}\n")
    return vault, tmpl, tmp_path


def test_render_template_file_returns_rendered(vault_and_template):
    vault, tmpl, _ = vault_and_template
    result = render_template_file(tmpl, vault, "prod", "secret")
    assert "host=db.example.com" in result
    assert "port=5432" in result


def test_render_template_file_writes_output(vault_and_template, tmp_path):
    vault, tmpl, base = vault_and_template
    out = base / "config.out"
    render_template_file(tmpl, vault, "prod", "secret", output_path=out)
    assert out.exists()
    content = out.read_text()
    assert "db.example.com" in content


def test_render_template_file_wrong_password(vault_and_template):
    vault, tmpl, _ = vault_and_template
    with pytest.raises(Exception):
        render_template_file(tmpl, vault, "prod", "wrong")
