"""Tests for envault.policy."""

from __future__ import annotations

import pytest

from envault.policy import (
    PolicyRule,
    PolicyViolation,
    enforce_policy,
    load_policy,
    save_policy,
)


@pytest.fixture
def vault_file(tmp_path):
    return str(tmp_path / "vault.env")


def test_save_and_load_policy_roundtrip(vault_file):
    rule = PolicyRule(min_length=8, require_uppercase=True, require_digit=True)
    save_policy(vault_file, "production", rule)
    loaded = load_policy(vault_file, "production")
    assert loaded is not None
    assert loaded.min_length == 8
    assert loaded.require_uppercase is True
    assert loaded.require_digit is True


def test_load_policy_returns_none_when_no_file(vault_file):
    result = load_policy(vault_file, "staging")
    assert result is None


def test_load_policy_returns_none_for_unknown_environment(vault_file):
    rule = PolicyRule(min_length=4)
    save_policy(vault_file, "dev", rule)
    assert load_policy(vault_file, "staging") is None


def test_multiple_environments_saved_independently(vault_file):
    save_policy(vault_file, "dev", PolicyRule(min_length=4))
    save_policy(vault_file, "prod", PolicyRule(min_length=16, require_special=True))
    dev = load_policy(vault_file, "dev")
    prod = load_policy(vault_file, "prod")
    assert dev.min_length == 4
    assert prod.min_length == 16
    assert prod.require_special is True


def test_enforce_policy_no_violations():
    rule = PolicyRule(min_length=4, require_digit=True)
    secrets = {"KEY": "abc1", "OTHER": "xyz9"}
    assert enforce_policy(secrets, rule) == []


def test_enforce_policy_min_length_violation():
    rule = PolicyRule(min_length=10)
    violations = enforce_policy({"SHORT": "abc"}, rule)
    assert len(violations) == 1
    assert violations[0].key == "SHORT"
    assert violations[0].rule == "min_length"


def test_enforce_policy_max_length_violation():
    rule = PolicyRule(max_length=5)
    violations = enforce_policy({"LONG": "abcdefgh"}, rule)
    assert any(v.rule == "max_length" for v in violations)


def test_enforce_policy_require_uppercase():
    rule = PolicyRule(require_uppercase=True)
    violations = enforce_policy({"K": "alllower"}, rule)
    assert any(v.rule == "require_uppercase" for v in violations)
    assert enforce_policy({"K": "HasUpper"}, rule) == []


def test_enforce_policy_require_digit():
    rule = PolicyRule(require_digit=True)
    assert enforce_policy({"K": "nodigits"}, rule) != []
    assert enforce_policy({"K": "has1digit"}, rule) == []


def test_enforce_policy_require_special():
    rule = PolicyRule(require_special=True)
    assert enforce_policy({"K": "nospecial"}, rule) != []
    assert enforce_policy({"K": "has!special"}, rule) == []


def test_enforce_policy_pattern():
    rule = PolicyRule(pattern=r"^prod-")
    assert enforce_policy({"K": "dev-value"}, rule) != []
    assert enforce_policy({"K": "prod-value"}, rule) == []


def test_enforce_policy_forbidden_pattern():
    rule = PolicyRule(forbidden_patterns=[r"password", r"secret"])
    violations = enforce_policy({"K": "mypassword123"}, rule)
    assert any(v.rule == "forbidden_pattern" for v in violations)
    assert enforce_policy({"K": "safe_value"}, rule) == []


def test_enforce_policy_multiple_violations_same_key():
    rule = PolicyRule(min_length=20, require_uppercase=True, require_digit=True)
    violations = enforce_policy({"K": "short"}, rule)
    rules_hit = {v.rule for v in violations}
    assert "min_length" in rules_hit
    assert "require_uppercase" in rules_hit
    assert "require_digit" in rules_hit
