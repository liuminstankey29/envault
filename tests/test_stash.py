"""Tests for envault.stash."""
from __future__ import annotations

import pytest

from envault.stash import (
    StashResult,
    stash_list,
    stash_pop,
    stash_push,
    stash_show,
)
from envault.vault import write_secrets, read_secrets


@pytest.fixture()
def vault_file(tmp_path):
    return str(tmp_path / "vault.json")


SECRETS = {"DB_URL": "postgres://localhost/db", "API_KEY": "abc123"}


def test_stash_push_returns_result(vault_file):
    result = stash_push(vault_file, "prod", SECRETS)
    assert isinstance(result, StashResult)
    assert result.count == 2
    assert set(result.keys) == {"DB_URL", "API_KEY"}
    assert result.stash_name == "default"


def test_stash_push_custom_name(vault_file):
    result = stash_push(vault_file, "prod", SECRETS, name="backup")
    assert result.stash_name == "backup"


def test_stash_show_returns_secrets(vault_file):
    stash_push(vault_file, "prod", SECRETS)
    shown = stash_show(vault_file, "prod")
    assert shown == SECRETS


def test_stash_show_returns_none_when_missing(vault_file):
    assert stash_show(vault_file, "prod", name="ghost") is None


def test_stash_show_does_not_remove_slot(vault_file):
    stash_push(vault_file, "prod", SECRETS)
    stash_show(vault_file, "prod")
    assert stash_show(vault_file, "prod") == SECRETS


def test_stash_pop_returns_secrets(vault_file):
    stash_push(vault_file, "prod", SECRETS)
    popped = stash_pop(vault_file, "prod")
    assert popped == SECRETS


def test_stash_pop_removes_slot(vault_file):
    stash_push(vault_file, "prod", SECRETS)
    stash_pop(vault_file, "prod")
    assert stash_show(vault_file, "prod") is None


def test_stash_pop_returns_none_when_missing(vault_file):
    assert stash_pop(vault_file, "prod", name="nope") is None


def test_stash_list_empty_when_no_stashes(vault_file):
    assert stash_list(vault_file) == []


def test_stash_list_returns_all_slots(vault_file):
    stash_push(vault_file, "prod", SECRETS, name="a")
    stash_push(vault_file, "staging", SECRETS, name="b")
    slots = stash_list(vault_file)
    assert "prod/a" in slots
    assert "staging/b" in slots


def test_stash_list_filtered_by_environment(vault_file):
    stash_push(vault_file, "prod", SECRETS, name="x")
    stash_push(vault_file, "staging", SECRETS, name="y")
    slots = stash_list(vault_file, environment="prod")
    assert all(s.startswith("prod/") for s in slots)
    assert len(slots) == 1


def test_multiple_named_stashes_coexist(vault_file):
    stash_push(vault_file, "prod", {"A": "1"}, name="first")
    stash_push(vault_file, "prod", {"B": "2"}, name="second")
    assert stash_show(vault_file, "prod", name="first") == {"A": "1"}
    assert stash_show(vault_file, "prod", name="second") == {"B": "2"}
