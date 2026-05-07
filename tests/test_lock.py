"""Tests for envault.lock module."""

import pytest
from pathlib import Path

from envault.lock import (
    lock_environment,
    unlock_environment,
    is_locked,
    get_lock_info,
    list_locked_environments,
    EnvironmentLockedError,
)


@pytest.fixture
def vault_file(tmp_path):
    return str(tmp_path / "test.vault")


def test_lock_environment_persists(vault_file):
    lock_environment(vault_file, "production")
    assert is_locked(vault_file, "production")


def test_lock_with_reason(vault_file):
    lock_environment(vault_file, "staging", reason="deploy freeze")
    info = get_lock_info(vault_file, "staging")
    assert info["reason"] == "deploy freeze"


def test_unlock_returns_true_when_was_locked(vault_file):
    lock_environment(vault_file, "dev")
    result = unlock_environment(vault_file, "dev")
    assert result is True


def test_unlock_returns_false_when_not_locked(vault_file):
    result = unlock_environment(vault_file, "nonexistent")
    assert result is False


def test_is_locked_false_after_unlock(vault_file):
    lock_environment(vault_file, "dev")
    unlock_environment(vault_file, "dev")
    assert not is_locked(vault_file, "dev")


def test_get_lock_info_none_when_not_locked(vault_file):
    assert get_lock_info(vault_file, "dev") is None


def test_list_locked_environments_empty(vault_file):
    assert list_locked_environments(vault_file) == {}


def test_list_locked_environments_multiple(vault_file):
    lock_environment(vault_file, "prod", reason="freeze")
    lock_environment(vault_file, "staging")
    locks = list_locked_environments(vault_file)
    assert "prod" in locks
    assert "staging" in locks
    assert len(locks) == 2


def test_lock_idempotent(vault_file):
    lock_environment(vault_file, "prod", reason="first")
    lock_environment(vault_file, "prod", reason="second")
    info = get_lock_info(vault_file, "prod")
    assert info["reason"] == "second"


def test_lock_file_created_next_to_vault(tmp_path, vault_file):
    lock_environment(vault_file, "prod")
    lock_file = tmp_path / "test.locks.json"
    assert lock_file.exists()


def test_environment_locked_error_is_runtime_error():
    assert issubclass(EnvironmentLockedError, RuntimeError)
