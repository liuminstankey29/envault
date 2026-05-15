"""Tests for envault.notify."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.notify import (
    add_notify_hook,
    fire_event,
    list_notify_hooks,
    remove_notify_hook,
    NotifyResult,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> str:
    return str(tmp_path / "vault.enc")


def test_add_hook_returns_true_when_new(vault_file: str) -> None:
    assert add_notify_hook(vault_file, "rotate", "https://example.com/hook") is True


def test_add_hook_returns_false_when_duplicate(vault_file: str) -> None:
    add_notify_hook(vault_file, "rotate", "https://example.com/hook")
    assert add_notify_hook(vault_file, "rotate", "https://example.com/hook") is False


def test_add_hook_persists(vault_file: str) -> None:
    add_notify_hook(vault_file, "expire", "https://a.example.com")
    hooks = list_notify_hooks(vault_file)
    assert "https://a.example.com" in hooks["expire"]


def test_multiple_events_stored_separately(vault_file: str) -> None:
    add_notify_hook(vault_file, "set", "https://s.example.com")
    add_notify_hook(vault_file, "rotate", "https://r.example.com")
    hooks = list_notify_hooks(vault_file)
    assert "https://s.example.com" in hooks["set"]
    assert "https://r.example.com" in hooks["rotate"]


def test_remove_hook_returns_true_when_existed(vault_file: str) -> None:
    add_notify_hook(vault_file, "set", "https://x.example.com")
    assert remove_notify_hook(vault_file, "set", "https://x.example.com") is True


def test_remove_hook_returns_false_when_missing(vault_file: str) -> None:
    assert remove_notify_hook(vault_file, "set", "https://nope.example.com") is False


def test_remove_hook_cleans_empty_event(vault_file: str) -> None:
    add_notify_hook(vault_file, "set", "https://x.example.com")
    remove_notify_hook(vault_file, "set", "https://x.example.com")
    hooks = list_notify_hooks(vault_file)
    assert "set" not in hooks


def test_list_hooks_empty_when_no_file(vault_file: str) -> None:
    assert list_notify_hooks(vault_file) == {}


def test_fire_event_no_hooks_returns_empty(vault_file: str) -> None:
    results = fire_event(vault_file, "rotate", {"env": "prod"})
    assert results == []


def test_fire_event_success(vault_file: str) -> None:
    add_notify_hook(vault_file, "rotate", "https://hook.example.com")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        results = fire_event(vault_file, "rotate", {"env": "prod"})
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].status_code == 200


def test_fire_event_failure_captured(vault_file: str) -> None:
    import urllib.error

    add_notify_hook(vault_file, "expire", "https://bad.example.com")
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url="https://bad.example.com", code=500, msg="err", hdrs=None, fp=None  # type: ignore[arg-type]
    )):
        results = fire_event(vault_file, "expire", {})
    assert results[0].success is False
    assert results[0].status_code == 500
