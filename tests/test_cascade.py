"""Tests for envault.cascade."""
from __future__ import annotations

import pytest

from envault.vault import write_secrets
from envault.cascade import cascade_environments, CascadeResult


@pytest.fixture()
def vault_file(tmp_path):
    return str(tmp_path / "vault.json")


def test_cascade_first_env_wins(vault_file):
    write_secrets(vault_file, "prod", "prodpass", {"DB_URL": "prod-db", "API_KEY": "prod-key"})
    write_secrets(vault_file, "staging", "stagpass", {"DB_URL": "staging-db", "EXTRA": "staging-extra"})

    result = cascade_environments(
        vault_file,
        [("prod", "prodpass"), ("staging", "stagpass")],
    )

    assert result.resolved["DB_URL"] == "prod-db"
    assert result.sources["DB_URL"] == "prod"


def test_cascade_fills_missing_from_lower_priority(vault_file):
    write_secrets(vault_file, "prod", "prodpass", {"API_KEY": "prod-key"})
    write_secrets(vault_file, "staging", "stagpass", {"DB_URL": "staging-db", "API_KEY": "stag-key"})

    result = cascade_environments(
        vault_file,
        [("prod", "prodpass"), ("staging", "stagpass")],
    )

    assert result.resolved["DB_URL"] == "staging-db"
    assert result.sources["DB_URL"] == "staging"
    assert result.resolved["API_KEY"] == "prod-key"


def test_cascade_keys_filter(vault_file):
    write_secrets(vault_file, "prod", "prodpass", {"A": "1", "B": "2", "C": "3"})

    result = cascade_environments(
        vault_file,
        [("prod", "prodpass")],
        keys=["A", "C"],
    )

    assert set(result.resolved.keys()) == {"A", "C"}
    assert "B" not in result.resolved


def test_cascade_bad_password_skipped(vault_file):
    write_secrets(vault_file, "prod", "prodpass", {"KEY": "value"})
    write_secrets(vault_file, "dev", "devpass", {"OTHER": "devval"})

    result = cascade_environments(
        vault_file,
        [("prod", "WRONG"), ("dev", "devpass")],
    )

    assert "prod" in result.skipped
    assert result.resolved.get("OTHER") == "devval"


def test_cascade_total_count(vault_file):
    write_secrets(vault_file, "base", "pass", {"X": "1", "Y": "2"})

    result = cascade_environments(vault_file, [("base", "pass")])

    assert result.total == 2


def test_cascade_empty_environments(vault_file):
    result = cascade_environments(vault_file, [])
    assert result.resolved == {}
    assert result.skipped == []
