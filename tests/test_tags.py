"""Tests for envault.tags module."""

from __future__ import annotations

import os
import pytest

from envault.vault import write_secrets
from envault.tags import add_tag, remove_tag, list_tags, filter_by_tag


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "test.enc")
    password = "testpass"
    write_secrets(path, "prod", password, {"DB_URL": "postgres://", "API_KEY": "secret"})
    return path, password


def test_add_tag_persists(vault_file):
    path, pw = vault_file
    add_tag(path, "prod", pw, "DB_URL", "database")
    tags = list_tags(path, "prod", pw, "DB_URL")
    assert "database" in tags


def test_add_tag_idempotent(vault_file):
    path, pw = vault_file
    add_tag(path, "prod", pw, "DB_URL", "database")
    add_tag(path, "prod", pw, "DB_URL", "database")
    tags = list_tags(path, "prod", pw, "DB_URL")
    assert tags.count("database") == 1


def test_add_tag_missing_key_raises(vault_file):
    path, pw = vault_file
    with pytest.raises(KeyError, match="MISSING_KEY"):
        add_tag(path, "prod", pw, "MISSING_KEY", "sometag")


def test_multiple_tags_on_same_key(vault_file):
    path, pw = vault_file
    add_tag(path, "prod", pw, "API_KEY", "sensitive")
    add_tag(path, "prod", pw, "API_KEY", "external")
    tags = list_tags(path, "prod", pw, "API_KEY")
    assert "sensitive" in tags
    assert "external" in tags


def test_remove_tag_returns_true_when_present(vault_file):
    path, pw = vault_file
    add_tag(path, "prod", pw, "DB_URL", "database")
    result = remove_tag(path, "prod", pw, "DB_URL", "database")
    assert result is True
    assert list_tags(path, "prod", pw, "DB_URL") == []


def test_remove_tag_returns_false_when_absent(vault_file):
    path, pw = vault_file
    result = remove_tag(path, "prod", pw, "DB_URL", "nonexistent")
    assert result is False


def test_list_tags_empty_for_untagged_key(vault_file):
    path, pw = vault_file
    assert list_tags(path, "prod", pw, "API_KEY") == []


def test_filter_by_tag_returns_matching_secrets(vault_file):
    path, pw = vault_file
    add_tag(path, "prod", pw, "DB_URL", "database")
    add_tag(path, "prod", pw, "API_KEY", "sensitive")
    result = filter_by_tag(path, "prod", pw, "database")
    assert "DB_URL" in result
    assert "API_KEY" not in result


def test_filter_by_tag_excludes_meta_key(vault_file):
    path, pw = vault_file
    add_tag(path, "prod", pw, "DB_URL", "database")
    result = filter_by_tag(path, "prod", pw, "database")
    from envault.tags import TAGS_KEY
    assert TAGS_KEY not in result


def test_filter_by_tag_empty_when_no_matches(vault_file):
    path, pw = vault_file
    result = filter_by_tag(path, "prod", pw, "nonexistent-tag")
    assert result == {}
