"""Tests for envault.cli_lint."""
from __future__ import annotations

import sys
import pytest

from envault.vault import write_secrets
from envault.cli_lint import cmd_lint, register_lint_parser


PASSWORD = 'clitest'


class Args:
    def __init__(self, vault, env, password, min_length=1):
        self.vault = vault
        self.env = env
        self.password = password
        self.min_length = min_length


@pytest.fixture
def vault_and_env(tmp_path):
    vault = str(tmp_path / 'vault.json')
    write_secrets(vault, 'prod', PASSWORD, {'DB_HOST': 'db.example.com'})
    return vault


def test_cmd_lint_clean_exits_zero(vault_and_env, capsys):
    args = Args(vault_and_env, 'prod', PASSWORD)
    cmd_lint(args)  # should not raise / call sys.exit
    out = capsys.readouterr().out
    assert 'No issues' in out


def test_cmd_lint_errors_exits_2(vault_and_env, capsys):
    write_secrets(vault_and_env, 'prod', PASSWORD, {'BAD': 'changeme'})
    args = Args(vault_and_env, 'prod', PASSWORD)
    with pytest.raises(SystemExit) as exc_info:
        cmd_lint(args)
    assert exc_info.value.code == 2


def test_cmd_lint_missing_vault_exits_1(tmp_path, capsys):
    args = Args(str(tmp_path / 'no.json'), 'prod', PASSWORD)
    with pytest.raises(SystemExit) as exc_info:
        cmd_lint(args)
    assert exc_info.value.code == 1


def test_register_lint_parser():
    import argparse
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    register_lint_parser(sub)
    parsed = root.parse_args(['lint', 'vault.json', 'dev', '--password', 'pw'])
    assert parsed.vault == 'vault.json'
    assert parsed.env == 'dev'
    assert parsed.password == 'pw'
    assert parsed.min_length == 1


def test_register_lint_parser_min_length():
    import argparse
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    register_lint_parser(sub)
    parsed = root.parse_args(['lint', 'v.json', 'env', '--password', 'pw', '--min-length', '16'])
    assert parsed.min_length == 16
