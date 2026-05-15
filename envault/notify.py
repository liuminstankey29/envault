"""Notification hooks: send alerts when secrets change, expire, or are accessed."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class NotifyResult:
    url: str
    status_code: int | None
    success: bool
    error: str | None = None


def _notify_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".notify.json")


def _load_hooks(vault_path: str) -> dict[str, list[str]]:
    p = _notify_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_hooks(vault_path: str, hooks: dict[str, list[str]]) -> None:
    _notify_path(vault_path).write_text(json.dumps(hooks, indent=2))


def add_notify_hook(vault_path: str, event: str, url: str) -> bool:
    """Register *url* for *event*. Returns True if newly added."""
    hooks = _load_hooks(vault_path)
    bucket = hooks.setdefault(event, [])
    if url in bucket:
        return False
    bucket.append(url)
    _save_hooks(vault_path, hooks)
    return True


def remove_notify_hook(vault_path: str, event: str, url: str) -> bool:
    """Remove *url* from *event*. Returns True if it existed."""
    hooks = _load_hooks(vault_path)
    bucket = hooks.get(event, [])
    if url not in bucket:
        return False
    bucket.remove(url)
    if not bucket:
        hooks.pop(event, None)
    _save_hooks(vault_path, hooks)
    return True


def list_notify_hooks(vault_path: str) -> dict[str, list[str]]:
    return _load_hooks(vault_path)


def fire_event(
    vault_path: str,
    event: str,
    payload: dict[str, Any],
    timeout: int = 5,
) -> list[NotifyResult]:
    """POST JSON *payload* to every URL registered for *event*."""
    hooks = _load_hooks(vault_path)
    results: list[NotifyResult] = []
    for url in hooks.get(event, []):
        body = json.dumps({"event": event, **payload}).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                results.append(NotifyResult(url=url, status_code=resp.status, success=True))
        except urllib.error.HTTPError as exc:
            results.append(NotifyResult(url=url, status_code=exc.code, success=False, error=str(exc)))
        except Exception as exc:  # noqa: BLE001
            results.append(NotifyResult(url=url, status_code=None, success=False, error=str(exc)))
    return results
