"""TTL (time-to-live) / expiry support for secrets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

_TTL_SUFFIX = ".ttl.json"


def _ttl_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix("").with_suffix(_TTL_SUFFIX)


def _load_ttl_map(vault_path: str) -> Dict[str, Dict[str, str]]:
    p = _ttl_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_ttl_map(vault_path: str, data: Dict[str, Dict[str, str]]) -> None:
    _ttl_path(vault_path).write_text(json.dumps(data, indent=2))


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def set_expiry(vault_path: str, environment: str, key: str, expires_at: datetime) -> None:
    """Record an expiry timestamp for a secret key in an environment."""
    data = _load_ttl_map(vault_path)
    env_map = data.setdefault(environment, {})
    env_map[key] = expires_at.isoformat()
    _save_ttl_map(vault_path, data)


def clear_expiry(vault_path: str, environment: str, key: str) -> bool:
    """Remove the expiry for a key. Returns True if an entry was removed."""
    data = _load_ttl_map(vault_path)
    removed = data.get(environment, {}).pop(key, None) is not None
    if removed:
        _save_ttl_map(vault_path, data)
    return removed


def get_expiry(vault_path: str, environment: str, key: str) -> Optional[datetime]:
    """Return the expiry datetime for a key, or None if not set."""
    data = _load_ttl_map(vault_path)
    raw = data.get(environment, {}).get(key)
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def list_expired(vault_path: str, environment: str) -> List[str]:
    """Return keys whose TTL has passed."""
    data = _load_ttl_map(vault_path)
    now = _now_utc()
    expired = []
    for key, ts in data.get(environment, {}).items():
        if datetime.fromisoformat(ts) <= now:
            expired.append(key)
    return expired


def list_all_expiries(vault_path: str, environment: str) -> Dict[str, datetime]:
    """Return all expiry datetimes for an environment."""
    data = _load_ttl_map(vault_path)
    return {
        k: datetime.fromisoformat(v)
        for k, v in data.get(environment, {}).items()
    }
