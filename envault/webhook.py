"""Webhook delivery for vault events."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _webhook_path(vault_file: str) -> Path:
    return Path(vault_file).with_suffix(".webhooks.json")


def _load_hooks(vault_file: str) -> dict[str, Any]:
    p = _webhook_path(vault_file)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_hooks(vault_file: str, data: dict[str, Any]) -> None:
    _webhook_path(vault_file).write_text(json.dumps(data, indent=2))


@dataclass
class WebhookResult:
    url: str
    status_code: int
    success: bool
    error: str = ""


def register_webhook(vault_file: str, name: str, url: str, events: list[str] | None = None) -> bool:
    """Register a named webhook. Returns True if newly added, False if updated."""
    hooks = _load_hooks(vault_file)
    is_new = name not in hooks
    hooks[name] = {"url": url, "events": events or ["*"]}
    _save_hooks(vault_file, hooks)
    return is_new


def remove_webhook(vault_file: str, name: str) -> bool:
    """Remove a webhook by name. Returns True if it existed."""
    hooks = _load_hooks(vault_file)
    if name not in hooks:
        return False
    del hooks[name]
    _save_hooks(vault_file, hooks)
    return True


def list_webhooks(vault_file: str) -> dict[str, Any]:
    """Return all registered webhooks."""
    return _load_hooks(vault_file)


def deliver_webhook(
    vault_file: str,
    event: str,
    payload: dict[str, Any],
    timeout: int = 5,
) -> list[WebhookResult]:
    """Deliver an event to all matching webhooks. Returns list of results."""
    hooks = _load_hooks(vault_file)
    results: list[WebhookResult] = []
    body = json.dumps({"event": event, **payload}).encode()

    for name, cfg in hooks.items():
        allowed = cfg.get("events", ["*"])
        if "*" not in allowed and event not in allowed:
            continue
        url = cfg["url"]
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "X-Envault-Event": event},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                results.append(WebhookResult(url=url, status_code=resp.status, success=True))
        except urllib.error.HTTPError as exc:
            results.append(WebhookResult(url=url, status_code=exc.code, success=False, error=str(exc)))
        except Exception as exc:  # noqa: BLE001
            results.append(WebhookResult(url=url, status_code=0, success=False, error=str(exc)))
    return results
