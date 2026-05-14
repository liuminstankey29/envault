"""Tests for envault.cli_redact (cmd_redact)."""
import sys
import types
import tempfile
import os
import pytest

from envault.vault import write_secrets
from envault.cli_redact import cmd_redact


class Args:
    def __init__(self, **kwargs):
        defaults = dict(
            vault=None,
            environment="prod",
            password="pw",
            text=None,
            file=None,
            output=None,
            mask="[REDACTED]",
            min_length=3,
            ignore=None,
            quiet=True,
        )
        defaults.update(kwargs)
        for k, v in defaults.items():
            setattr(self, k, v)


@pytest.fixture()
def vault_and_env(tmp_path):
    vf = str(tmp_path / "vault.enc")
    write_secrets(vf, "prod", "pw", {"DB_PASS": "supersecret", "API_KEY": "abc123xyz"})
    return vf


def test_cmd_redact_inline_text(vault_and_env, capsys):
    args = Args(vault=vault_and_env, text="password is supersecret end")
    cmd_redact(args)
    out = capsys.readouterr().out
    assert "supersecret" not in out
    assert "[REDACTED]" in out


def test_cmd_redact_from_file(vault_and_env, tmp_path, capsys):
    src = tmp_path / "log.txt"
    src.write_text("token abc123xyz here")
    args = Args(vault=vault_and_env, file=str(src))
    cmd_redact(args)
    out = capsys.readouterr().out
    assert "abc123xyz" not in out
    assert "[REDACTED]" in out


def test_cmd_redact_writes_output_file(vault_and_env, tmp_path, capsys):
    src = tmp_path / "input.txt"
    dst = tmp_path / "output.txt"
    src.write_text("supersecret")
    args = Args(vault=vault_and_env, file=str(src), output=str(dst))
    cmd_redact(args)
    assert dst.read_text() == "[REDACTED]"


def test_cmd_redact_custom_mask(vault_and_env, capsys):
    args = Args(vault=vault_and_env, text="supersecret", mask="***")
    cmd_redact(args)
    out = capsys.readouterr().out
    assert "***" in out


def test_cmd_redact_bad_vault_exits_1(tmp_path):
    args = Args(vault=str(tmp_path / "missing.enc"), text="hello")
    with pytest.raises(SystemExit) as exc:
        cmd_redact(args)
    assert exc.value.code == 1


def test_cmd_redact_ignore_keys(vault_and_env, capsys):
    args = Args(vault=vault_and_env, text="supersecret", ignore=["DB_PASS"])
    cmd_redact(args)
    out = capsys.readouterr().out
    assert "supersecret" in out
