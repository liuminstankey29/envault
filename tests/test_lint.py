"""Tests for envault.lint."""
from __future__ import annotations

import pytest

from envault.vault import write_secrets
from envault.lint import lint_secrets, format_lint_results, LintIssue


@pytest.fixture
def vault_file(tmp_path):
    return str(tmp_path / 'vault.json')


PASSWORD = 'lintpass'


def _write(vault_file, env, secrets):
    for k, v in secrets.items():
        write_secrets(vault_file, env, PASSWORD, {k: v})


def test_no_issues_for_clean_secrets(vault_file):
    _write(vault_file, 'prod', {'DB_URL': 'postgres://host/db', 'API_KEY': 'abc123'})
    issues = lint_secrets(vault_file, 'prod', PASSWORD)
    assert issues == []


def test_empty_value_is_error(vault_file):
    _write(vault_file, 'dev', {'EMPTY_KEY': ''})
    issues = lint_secrets(vault_file, 'dev', PASSWORD)
    assert any(i.key == 'EMPTY_KEY' and i.severity == 'error' for i in issues)


def test_placeholder_value_is_error(vault_file):
    for placeholder in ['changeme', 'CHANGEME', 'placeholder', 'xxx', 'TODO']:
        _write(vault_file, 'dev', {f'KEY_{placeholder}': placeholder})
    issues = lint_secrets(vault_file, 'dev', PASSWORD)
    error_keys = {i.key for i in issues if i.severity == 'error'}
    assert 'KEY_changeme' in error_keys
    assert 'KEY_placeholder' in error_keys


def test_lowercase_key_is_warning(vault_file):
    _write(vault_file, 'staging', {'bad_key': 'somevalue'})
    issues = lint_secrets(vault_file, 'staging', PASSWORD)
    assert any(i.key == 'bad_key' and i.severity == 'warning' for i in issues)


def test_whitespace_padding_is_warning(vault_file):
    _write(vault_file, 'qa', {'MY_SECRET': '  padded  '})
    issues = lint_secrets(vault_file, 'qa', PASSWORD)
    assert any(i.key == 'MY_SECRET' and 'whitespace' in i.message for i in issues)


def test_min_value_length_enforced(vault_file):
    _write(vault_file, 'prod', {'SHORT': 'ab'})
    issues = lint_secrets(vault_file, 'prod', PASSWORD, min_value_length=8)
    assert any(i.key == 'SHORT' and i.severity == 'error' for i in issues)


def test_format_no_issues():
    result = format_lint_results([])
    assert 'No issues' in result


def test_format_shows_all_issues():
    issues = [
        LintIssue('KEY_A', 'error', 'Value is empty'),
        LintIssue('KEY_B', 'warning', 'Whitespace'),
    ]
    result = format_lint_results(issues)
    assert 'KEY_A' in result
    assert 'KEY_B' in result
    assert '[ERROR]' in result
    assert '[WARN]' in result


def test_vault_not_found_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        lint_secrets(str(tmp_path / 'missing.json'), 'env', 'pw')
