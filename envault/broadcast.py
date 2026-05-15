"""broadcast.py – notify external endpoints when secrets change."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


def _broadcast_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".broadcasts.json")


def _load_hooks(vault_path: str) -> List[dict]:
    p = _broadcast_path(vault_path)
    if not p.exists():
        return []
    return json.loads(p.read_text())


def _save_hooks(vault_path: str, hooks: List[dict]) -> None:
    _broadcast_path(vault_path).write_text(json.dumps(hooks, indent=2))


@dataclass
class BroadcastResult:
    url: str
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


def add_hook(vault_path: str, url: str, events: Optional[List[str]] = None) -> bool:
    """Register a webhook URL. Returns True if newly added, False if updated."""
    hooks = _load_hooks(vault_path)
    for hook in hooks:
        if hook["url"] == url:
            hook["events"] = events or ["*"]
            _save_hooks(vault_path, hooks)
            return False
    hooks.append({"url": url, "events": events or ["*"]})
    _save_hooks(vault_path, hooks)
    return True


def remove_hook(vault_path: str, url: str) -> bool:
    """Remove a webhook URL. Returns True if it existed."""
    hooks = _load_hooks(vault_path)
    new_hooks = [h for h in hooks if h["url"] != url]
    if len(new_hooks) == len(hooks):
        return False
    _save_hooks(vault_path, new_hooks)
    return True


def list_hooks(vault_path: str) -> List[dict]:
    return _load_hooks(vault_path)


def broadcast_event(
    vault_path: str, event: str, payload: dict
) -> List[BroadcastResult]:
    """POST *payload* to every registered hook that matches *event*."""
    results: List[BroadcastResult] = []
    for hook in _load_hooks(vault_path):
        events = hook.get("events", ["*"])
        if "*" not in events and event not in events:
            continue
        body = json.dumps({"event": event, **payload}).encode()
        req = urllib.request.Request(
            hook["url"],
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                results.append(BroadcastResult(url=hook["url"], success=True, status_code=resp.status))
        except urllib.error.HTTPError as exc:
            results.append(BroadcastResult(url=hook["url"], success=False, status_code=exc.code, error=str(exc)))
        except Exception as exc:  # noqa: BLE001
            results.append(BroadcastResult(url=hook["url"], success=False, error=str(exc)))
    return results
