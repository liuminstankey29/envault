"""Tests for envault.broadcast."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.broadcast import (
    add_hook,
    remove_hook,
    list_hooks,
    broadcast_event,
    BroadcastResult,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> str:
    return str(tmp_path / "vault.env")


def test_add_hook_returns_true_when_new(vault_file):
    assert add_hook(vault_file, "https://example.com/hook") is True


def test_add_hook_returns_false_when_updated(vault_file):
    add_hook(vault_file, "https://example.com/hook")
    assert add_hook(vault_file, "https://example.com/hook") is False


def test_add_hook_persists(vault_file):
    add_hook(vault_file, "https://example.com/hook", events=["secret.changed"])
    hooks = list_hooks(vault_file)
    assert len(hooks) == 1
    assert hooks[0]["url"] == "https://example.com/hook"
    assert hooks[0]["events"] == ["secret.changed"]


def test_add_multiple_hooks(vault_file):
    add_hook(vault_file, "https://a.example.com")
    add_hook(vault_file, "https://b.example.com")
    assert len(list_hooks(vault_file)) == 2


def test_remove_hook_returns_true_when_existed(vault_file):
    add_hook(vault_file, "https://example.com/hook")
    assert remove_hook(vault_file, "https://example.com/hook") is True


def test_remove_hook_returns_false_when_missing(vault_file):
    assert remove_hook(vault_file, "https://missing.example.com") is False


def test_remove_hook_deletes_entry(vault_file):
    add_hook(vault_file, "https://example.com/hook")
    remove_hook(vault_file, "https://example.com/hook")
    assert list_hooks(vault_file) == []


def test_list_hooks_empty_when_no_file(vault_file):
    assert list_hooks(vault_file) == []


def _mock_response(status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_broadcast_event_calls_matching_hooks(vault_file):
    add_hook(vault_file, "https://example.com/hook", events=["secret.changed"])
    with patch("urllib.request.urlopen", return_value=_mock_response(200)) as mock_open:
        results = broadcast_event(vault_file, "secret.changed", {"key": "DB_PASS"})
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].status_code == 200
    mock_open.assert_called_once()


def test_broadcast_event_skips_non_matching_events(vault_file):
    add_hook(vault_file, "https://example.com/hook", events=["secret.rotated"])
    with patch("urllib.request.urlopen") as mock_open:
        results = broadcast_event(vault_file, "secret.changed", {})
    assert results == []
    mock_open.assert_not_called()


def test_broadcast_wildcard_hook_always_fires(vault_file):
    add_hook(vault_file, "https://example.com/hook")  # default events=["*"]
    with patch("urllib.request.urlopen", return_value=_mock_response(204)):
        results = broadcast_event(vault_file, "any.event", {})
    assert len(results) == 1
    assert results[0].success is True


def test_broadcast_records_failure_on_exception(vault_file):
    add_hook(vault_file, "https://example.com/hook")
    with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
        results = broadcast_event(vault_file, "any.event", {})
    assert len(results) == 1
    assert results[0].success is False
    assert "timeout" in results[0].error
