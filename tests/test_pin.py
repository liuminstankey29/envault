"""Tests for envault.pin"""

import pytest

from envault.pin import (
    assert_not_pinned,
    is_pinned,
    list_pins,
    pin_secret,
    unpin_secret,
)


@pytest.fixture()
def vault_file(tmp_path):
    return str(tmp_path / "vault.enc")


def test_pin_secret_returns_true_when_newly_pinned(vault_file):
    assert pin_secret(vault_file, "prod", "DB_PASS") is True


def test_pin_secret_returns_false_when_already_pinned(vault_file):
    pin_secret(vault_file, "prod", "DB_PASS")
    assert pin_secret(vault_file, "prod", "DB_PASS") is False


def test_is_pinned_true_after_pin(vault_file):
    pin_secret(vault_file, "prod", "API_KEY")
    assert is_pinned(vault_file, "prod", "API_KEY") is True


def test_is_pinned_false_before_pin(vault_file):
    assert is_pinned(vault_file, "prod", "MISSING") is False


def test_is_pinned_false_after_unpin(vault_file):
    pin_secret(vault_file, "staging", "SECRET")
    unpin_secret(vault_file, "staging", "SECRET")
    assert is_pinned(vault_file, "staging", "SECRET") is False


def test_unpin_returns_true_when_was_pinned(vault_file):
    pin_secret(vault_file, "dev", "TOKEN")
    assert unpin_secret(vault_file, "dev", "TOKEN") is True


def test_unpin_returns_false_when_not_pinned(vault_file):
    assert unpin_secret(vault_file, "dev", "GHOST") is False


def test_list_pins_empty_initially(vault_file):
    assert list_pins(vault_file, "prod") == []


def test_list_pins_shows_all_pinned_keys(vault_file):
    pin_secret(vault_file, "prod", "KEY_A")
    pin_secret(vault_file, "prod", "KEY_B")
    pins = list_pins(vault_file, "prod")
    assert "KEY_A" in pins
    assert "KEY_B" in pins
    assert len(pins) == 2


def test_list_pins_isolated_per_environment(vault_file):
    pin_secret(vault_file, "prod", "SHARED")
    assert list_pins(vault_file, "staging") == []


def test_assert_not_pinned_passes_when_not_pinned(vault_file):
    # Should not raise
    assert_not_pinned(vault_file, "prod", "FREE_KEY")


def test_assert_not_pinned_raises_when_pinned(vault_file):
    pin_secret(vault_file, "prod", "LOCKED")
    with pytest.raises(ValueError, match="pinned"):
        assert_not_pinned(vault_file, "prod", "LOCKED")


def test_pin_file_cleaned_up_when_last_pin_removed(vault_file):
    from envault.pin import _pin_path
    pin_secret(vault_file, "dev", "ONLY_KEY")
    unpin_secret(vault_file, "dev", "ONLY_KEY")
    pin_map_path = _pin_path(vault_file)
    # File may exist but env key should be absent
    if pin_map_path.exists():
        import json
        data = json.loads(pin_map_path.read_text())
        assert "dev" not in data
