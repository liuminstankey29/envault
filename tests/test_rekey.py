"""Tests for envault.rekey."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import write_secrets, read_secrets
from envault.rekey import rekey_environment, rekey_all_environments, RekeyResult


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    return tmp_path / "vault.db"


def test_rekey_environment_returns_result(vault_file: Path) -> None:
    write_secrets(vault_file, "prod", "old", {"KEY": "val"})
    result = rekey_environment(vault_file, "prod", "old", "new")
    assert isinstance(result, RekeyResult)
    assert result.environment == "prod"
    assert result.secrets_rekeyed == 1
    assert not result.skipped


def test_secrets_readable_with_new_password(vault_file: Path) -> None:
    write_secrets(vault_file, "prod", "old", {"A": "1", "B": "2"})
    rekey_environment(vault_file, "prod", "old", "new")
    secrets = read_secrets(vault_file, "prod", "new")
    assert secrets == {"A": "1", "B": "2"}


def test_old_password_rejected_after_rekey(vault_file: Path) -> None:
    write_secrets(vault_file, "prod", "old", {"X": "y"})
    rekey_environment(vault_file, "prod", "old", "new")
    with pytest.raises(Exception):
        read_secrets(vault_file, "prod", "old")


def test_wrong_old_password_raises(vault_file: Path) -> None:
    write_secrets(vault_file, "prod", "correct", {"K": "v"})
    with pytest.raises(Exception):
        rekey_environment(vault_file, "prod", "wrong", "new")


def test_rekey_all_environments(vault_file: Path) -> None:
    write_secrets(vault_file, "dev", "old", {"D": "1"})
    write_secrets(vault_file, "staging", "old", {"S": "2", "T": "3"})
    results = rekey_all_environments(vault_file, "old", "new")
    assert len(results) == 2
    total = sum(r.secrets_rekeyed for r in results)
    assert total == 3


def test_rekey_all_skip_errors(vault_file: Path) -> None:
    write_secrets(vault_file, "dev", "old", {"D": "1"})
    write_secrets(vault_file, "staging", "different", {"S": "2"})
    results = rekey_all_environments(vault_file, "old", "new", skip_errors=True)
    skipped = [r for r in results if r.skipped]
    succeeded = [r for r in results if not r.skipped]
    assert len(skipped) == 1
    assert len(succeeded) == 1
    assert skipped[0].environment == "staging"


def test_rekey_all_raises_by_default_on_error(vault_file: Path) -> None:
    write_secrets(vault_file, "dev", "old", {"D": "1"})
    write_secrets(vault_file, "staging", "different", {"S": "2"})
    with pytest.raises(Exception):
        rekey_all_environments(vault_file, "old", "new", skip_errors=False)


def test_rekey_preserves_all_keys(vault_file: Path) -> None:
    original = {"ALPHA": "a", "BETA": "b", "GAMMA": "c"}
    write_secrets(vault_file, "prod", "old", original)
    rekey_environment(vault_file, "prod", "old", "new")
    assert read_secrets(vault_file, "prod", "new") == original
