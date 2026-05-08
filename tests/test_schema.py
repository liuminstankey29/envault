"""Tests for envault.schema — validate_secrets and format_validation_results."""
from __future__ import annotations

import pytest

from envault.schema import (
    SchemaRule,
    ValidationIssue,
    ValidationResult,
    validate_secrets,
    format_validation_results,
)


# ---------------------------------------------------------------------------
# validate_secrets
# ---------------------------------------------------------------------------

def test_no_issues_for_valid_secrets():
    rules = [SchemaRule(key="DB_URL", required=True)]
    result = validate_secrets({"DB_URL": "postgres://localhost/db"}, rules)
    assert result.ok
    assert result.issues == []


def test_missing_required_key_is_error():
    rules = [SchemaRule(key="API_KEY", required=True)]
    result = validate_secrets({}, rules)
    assert not result.ok
    assert any(i.key == "API_KEY" and i.severity == "error" for i in result.issues)


def test_missing_optional_key_is_not_error():
    rules = [SchemaRule(key="OPTIONAL", required=False)]
    result = validate_secrets({}, rules)
    assert result.ok
    assert result.issues == []


def test_pattern_mismatch_is_error():
    rules = [SchemaRule(key="PORT", pattern=r"\d+")]
    result = validate_secrets({"PORT": "abc"}, rules)
    assert not result.ok
    assert any(i.key == "PORT" for i in result.issues)


def test_pattern_match_passes():
    rules = [SchemaRule(key="PORT", pattern=r"\d+")]
    result = validate_secrets({"PORT": "5432"}, rules)
    assert result.ok


def test_min_length_violation():
    rules = [SchemaRule(key="SECRET", min_length=16)]
    result = validate_secrets({"SECRET": "short"}, rules)
    assert not result.ok
    assert any("too short" in i.message for i in result.issues)


def test_max_length_violation():
    rules = [SchemaRule(key="NAME", max_length=5)]
    result = validate_secrets({"NAME": "toolongname"}, rules)
    assert not result.ok
    assert any("too long" in i.message for i in result.issues)


def test_allowed_values_violation():
    rules = [SchemaRule(key="ENV", allowed_values=["prod", "staging"])]
    result = validate_secrets({"ENV": "dev"}, rules)
    assert not result.ok
    assert any(i.key == "ENV" for i in result.issues)


def test_allowed_values_passes():
    rules = [SchemaRule(key="ENV", allowed_values=["prod", "staging"])]
    result = validate_secrets({"ENV": "prod"}, rules)
    assert result.ok


def test_multiple_rules_multiple_errors():
    rules = [
        SchemaRule(key="A", required=True),
        SchemaRule(key="B", required=True),
    ]
    result = validate_secrets({}, rules)
    assert len(result.errors) == 2


# ---------------------------------------------------------------------------
# format_validation_results
# ---------------------------------------------------------------------------

def test_format_ok_shows_passed():
    result = ValidationResult()
    text = format_validation_results(result)
    assert "passed" in text.lower()


def test_format_errors_shown():
    result = ValidationResult(
        issues=[ValidationIssue("X", "error", "Something wrong.")]
    )
    text = format_validation_results(result)
    assert "[ERROR]" in text
    assert "X" in text
