"""Tests for envault.webhook."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from envault.webhook import (
    WebhookResult,
    deliver_webhook,
    list_webhooks,
    register_webhook,
    remove_webhook,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> str:
    return str(tmp_path / "secrets.vault")


def test_register_webhook_returns_true_when_new(vault_file: str) -> None:
    result = register_webhook(vault_file, "slack", "https://hooks.example.com/slack")
    assert result is True


def test_register_webhook_returns_false_when_updated(vault_file: str) -> None:
    register_webhook(vault_file, "slack", "https://hooks.example.com/slack")
    result = register_webhook(vault_file, "slack", "https://hooks.example.com/slack-v2")
    assert result is False


def test_register_webhook_persists(vault_file: str) -> None:
    register_webhook(vault_file, "teams", "https://hooks.example.com/teams", events=["rotate"])
    hooks = list_webhooks(vault_file)
    assert "teams" in hooks
    assert hooks["teams"]["url"] == "https://hooks.example.com/teams"
    assert hooks["teams"]["events"] == ["rotate"]


def test_register_webhook_default_events_is_wildcard(vault_file: str) -> None:
    register_webhook(vault_file, "svc", "https://example.com")
    hooks = list_webhooks(vault_file)
    assert hooks["svc"]["events"] == ["*"]


def test_remove_webhook_returns_true_when_existed(vault_file: str) -> None:
    register_webhook(vault_file, "pagerduty", "https://pd.example.com")
    assert remove_webhook(vault_file, "pagerduty") is True


def test_remove_webhook_returns_false_when_missing(vault_file: str) -> None:
    assert remove_webhook(vault_file, "nonexistent") is False


def test_remove_webhook_deletes_entry(vault_file: str) -> None:
    register_webhook(vault_file, "svc", "https://example.com")
    remove_webhook(vault_file, "svc")
    assert "svc" not in list_webhooks(vault_file)


def test_list_webhooks_empty_when_no_file(vault_file: str) -> None:
    assert list_webhooks(vault_file) == {}


def test_deliver_webhook_calls_matching_hooks(vault_file: str) -> None:
    register_webhook(vault_file, "svc", "https://example.com", events=["rotate"])
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        results = deliver_webhook(vault_file, "rotate", {"env": "prod"})
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].status_code == 200
    mock_open.assert_called_once()


def test_deliver_webhook_skips_non_matching_event(vault_file: str) -> None:
    register_webhook(vault_file, "svc", "https://example.com", events=["rotate"])
    with patch("urllib.request.urlopen") as mock_open:
        results = deliver_webhook(vault_file, "set", {})
    assert results == []
    mock_open.assert_not_called()


def test_deliver_webhook_wildcard_matches_any_event(vault_file: str) -> None:
    register_webhook(vault_file, "svc", "https://example.com")  # default: ["*"]
    mock_resp = MagicMock()
    mock_resp.status = 204
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        results = deliver_webhook(vault_file, "anything", {})
    assert len(results) == 1
    assert results[0].success is True


def test_deliver_webhook_records_failure_on_exception(vault_file: str) -> None:
    register_webhook(vault_file, "svc", "https://example.com")
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        results = deliver_webhook(vault_file, "rotate", {})
    assert len(results) == 1
    assert results[0].success is False
    assert "connection refused" in results[0].error
    assert results[0].status_code == 0
