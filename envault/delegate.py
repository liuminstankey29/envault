"""Delegate: grant read-only or read-write access tokens for an environment."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


def _delegate_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".delegates.json")


def _load_delegate_map(vault_path: str) -> dict:
    p = _delegate_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_delegate_map(vault_path: str, data: dict) -> None:
    _delegate_path(vault_path).write_text(json.dumps(data, indent=2))


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass
class DelegateEntry:
    token_hash: str
    environment: str
    access: str          # "read" or "write"
    created_at: float
    expires_at: Optional[float]
    label: str = ""


def create_delegate(
    vault_path: str,
    environment: str,
    access: str = "read",
    ttl_seconds: Optional[int] = None,
    label: str = "",
) -> str:
    """Create a delegate token and persist it.  Returns the raw token."""
    if access not in ("read", "write"):
        raise ValueError(f"access must be 'read' or 'write', got {access!r}")
    token = secrets.token_urlsafe(32)
    thash = _token_hash(token)
    now = time.time()
    entry = {
        "environment": environment,
        "access": access,
        "created_at": now,
        "expires_at": now + ttl_seconds if ttl_seconds else None,
        "label": label,
    }
    data = _load_delegate_map(vault_path)
    data.setdefault(environment, {})[thash] = entry
    _save_delegate_map(vault_path, data)
    return token


def revoke_delegate(vault_path: str, environment: str, token: str) -> bool:
    """Revoke a delegate token.  Returns True if it existed."""
    data = _load_delegate_map(vault_path)
    thash = _token_hash(token)
    env_tokens = data.get(environment, {})
    if thash not in env_tokens:
        return False
    del env_tokens[thash]
    if not env_tokens:
        data.pop(environment, None)
    else:
        data[environment] = env_tokens
    _save_delegate_map(vault_path, data)
    return True


def validate_delegate(
    vault_path: str, environment: str, token: str, required_access: str = "read"
) -> bool:
    """Return True if token is valid, not expired, and has sufficient access."""
    data = _load_delegate_map(vault_path)
    thash = _token_hash(token)
    entry = data.get(environment, {}).get(thash)
    if entry is None:
        return False
    if entry["expires_at"] is not None and time.time() > entry["expires_at"]:
        return False
    if required_access == "write" and entry["access"] != "write":
        return False
    return True


def list_delegates(vault_path: str, environment: str) -> List[DelegateEntry]:
    """Return all delegate entries for an environment."""
    data = _load_delegate_map(vault_path)
    result = []
    for thash, entry in data.get(environment, {}).items():
        result.append(
            DelegateEntry(
                token_hash=thash,
                environment=environment,
                access=entry["access"],
                created_at=entry["created_at"],
                expires_at=entry["expires_at"],
                label=entry.get("label", ""),
            )
        )
    return result
