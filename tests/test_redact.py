"""Tests for envault.redact."""
import pytest

from envault.redact import redact_text, RedactResult


SECRETS = {
    "DB_PASS": "supersecret",
    "API_KEY": "abc123xyz",
    "SHORT": "ab",
    "TOKEN": "tok_live_ABCDEF",
}


def test_basic_redaction():
    result = redact_text("password is supersecret ok", SECRETS)
    assert "supersecret" not in result.redacted_text
    assert "[REDACTED]" in result.redacted_text
    assert result.matches == 1
    assert "DB_PASS" in result.redacted_keys


def test_multiple_occurrences_counted():
    result = redact_text("supersecret and supersecret", SECRETS)
    assert result.matches == 2
    assert result.redacted_text == "[REDACTED] and [REDACTED]"


def test_multiple_secrets_redacted():
    text = f"key={SECRETS['API_KEY']} pass={SECRETS['DB_PASS']}"
    result = redact_text(text, SECRETS)
    assert SECRETS["API_KEY"] not in result.redacted_text
    assert SECRETS["DB_PASS"] not in result.redacted_text
    assert len(result.redacted_keys) == 2


def test_min_value_length_skips_short_values():
    result = redact_text("ab is here", SECRETS, min_value_length=3)
    # 'ab' is only 2 chars, should NOT be redacted
    assert "ab" in result.redacted_text
    assert "SHORT" not in result.redacted_keys


def test_custom_mask():
    result = redact_text("supersecret", SECRETS, mask="***")
    assert result.redacted_text == "***"


def test_no_match_returns_original_text():
    result = redact_text("nothing sensitive here", SECRETS)
    assert result.redacted_text == "nothing sensitive here"
    assert result.matches == 0
    assert result.redacted_keys == []


def test_ignore_keys_skips_specified_keys():
    result = redact_text("supersecret abc123xyz", SECRETS, ignore_keys=["DB_PASS"])
    assert "supersecret" in result.redacted_text
    assert "abc123xyz" not in result.redacted_text
    assert "DB_PASS" not in result.redacted_keys
    assert "API_KEY" in result.redacted_keys


def test_longer_secret_replaced_before_shorter_overlap():
    secrets = {"A": "foobar", "B": "foo"}
    result = redact_text("foobar", secrets)
    # 'foobar' should be replaced as a whole, not 'foo' first leaving 'bar'
    assert result.redacted_text == "[REDACTED]"
    assert result.matches == 1


def test_empty_secrets_returns_unchanged():
    result = redact_text("hello world", {})
    assert result.redacted_text == "hello world"
    assert result.matches == 0


def test_empty_text_returns_empty():
    result = redact_text("", SECRETS)
    assert result.redacted_text == ""
    assert result.matches == 0


def test_returns_redact_result_type():
    result = redact_text("x", SECRETS)
    assert isinstance(result, RedactResult)
