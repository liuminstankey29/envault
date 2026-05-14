"""Tests for envault.access module."""
import pytest
from pathlib import Path

from envault.access import (
    AccessRule,
    can_read,
    can_write,
    get_access_rule,
    list_access_rules,
    remove_access_rule,
    set_access_rule,
)


@pytest.fixture
def vault_file(tmp_path):
    return str(tmp_path / "vault.env")


def test_set_and_get_access_rule(vault_file):
    rule = AccessRule(role="developer", environment="staging",
                      readable_keys=["DB_URL"], writable_keys=["APP_KEY"])
    set_access_rule(vault_file, rule)
    loaded = get_access_rule(vault_file, "staging", "developer")
    assert loaded is not None
    assert loaded.role == "developer"
    assert loaded.readable_keys == ["DB_URL"]
    assert loaded.writable_keys == ["APP_KEY"]


def test_get_access_rule_returns_none_when_missing(vault_file):
    result = get_access_rule(vault_file, "production", "admin")
    assert result is None


def test_set_access_rule_overwrites_existing(vault_file):
    rule1 = AccessRule(role="reader", environment="dev", readable_keys=["A"], writable_keys=[])
    rule2 = AccessRule(role="reader", environment="dev", readable_keys=["A", "B"], writable_keys=["C"])
    set_access_rule(vault_file, rule1)
    set_access_rule(vault_file, rule2)
    loaded = get_access_rule(vault_file, "dev", "reader")
    assert loaded.readable_keys == ["A", "B"]
    assert loaded.writable_keys == ["C"]


def test_remove_access_rule_returns_true_when_existed(vault_file):
    rule = AccessRule(role="ops", environment="prod", readable_keys=[], writable_keys=["SECRET"])
    set_access_rule(vault_file, rule)
    assert remove_access_rule(vault_file, "prod", "ops") is True


def test_remove_access_rule_returns_false_when_not_set(vault_file):
    assert remove_access_rule(vault_file, "prod", "ghost") is False


def test_remove_access_rule_makes_rule_unretrievable(vault_file):
    rule = AccessRule(role="dev", environment="test", readable_keys=["X"], writable_keys=[])
    set_access_rule(vault_file, rule)
    remove_access_rule(vault_file, "test", "dev")
    assert get_access_rule(vault_file, "test", "dev") is None


def test_list_access_rules_all(vault_file):
    set_access_rule(vault_file, AccessRule("r1", "envA", ["K1"], []))
    set_access_rule(vault_file, AccessRule("r2", "envB", ["K2"], ["K2"]))
    rules = list_access_rules(vault_file)
    assert len(rules) == 2


def test_list_access_rules_filtered_by_environment(vault_file):
    set_access_rule(vault_file, AccessRule("r1", "envA", [], []))
    set_access_rule(vault_file, AccessRule("r2", "envB", [], []))
    rules = list_access_rules(vault_file, environment="envA")
    assert all(r.environment == "envA" for r in rules)
    assert len(rules) == 1


def test_can_read_with_empty_readable_keys_allows_all(vault_file):
    set_access_rule(vault_file, AccessRule("admin", "prod", readable_keys=[], writable_keys=[]))
    assert can_read(vault_file, "prod", "admin", "ANY_KEY") is True


def test_can_read_restricted_to_specific_keys(vault_file):
    set_access_rule(vault_file, AccessRule("viewer", "prod", readable_keys=["DB_URL"], writable_keys=[]))
    assert can_read(vault_file, "prod", "viewer", "DB_URL") is True
    assert can_read(vault_file, "prod", "viewer", "SECRET_KEY") is False


def test_can_write_only_for_listed_keys(vault_file):
    set_access_rule(vault_file, AccessRule("editor", "dev", readable_keys=[], writable_keys=["TOKEN"]))
    assert can_write(vault_file, "dev", "editor", "TOKEN") is True
    assert can_write(vault_file, "dev", "editor", "OTHER") is False


def test_can_read_returns_false_for_unknown_role(vault_file):
    assert can_read(vault_file, "prod", "nobody", "KEY") is False


def test_can_write_returns_false_for_unknown_role(vault_file):
    assert can_write(vault_file, "prod", "nobody", "KEY") is False
