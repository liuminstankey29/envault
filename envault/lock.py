"""Environment locking — prevent writes to a specific environment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _lock_path(vault_file: str) -> Path:
    return Path(vault_file).with_suffix(".locks.json")


def _load_lock_map(vault_file: str) -> dict:
    p = _lock_path(vault_file)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_lock_map(vault_file: str, data: dict) -> None:
    _lock_path(vault_file).write_text(json.dumps(data, indent=2))


def lock_environment(vault_file: str, environment: str, reason: Optional[str] = None) -> dict:
    """Lock an environment, optionally recording a reason."""
    locks = _load_lock_map(vault_file)
    entry = {"locked": True, "reason": reason or ""}
    locks[environment] = entry
    _save_lock_map(vault_file, locks)
    return entry


def unlock_environment(vault_file: str, environment: str) -> bool:
    """Unlock an environment. Returns True if it was previously locked."""
    locks = _load_lock_map(vault_file)
    if environment not in locks:
        return False
    del locks[environment]
    _save_lock_map(vault_file, locks)
    return True


def is_locked(vault_file: str, environment: str) -> bool:
    """Return True if the environment is currently locked."""
    locks = _load_lock_map(vault_file)
    return locks.get(environment, {}).get("locked", False)


def get_lock_info(vault_file: str, environment: str) -> Optional[dict]:
    """Return lock metadata for an environment, or None if not locked."""
    locks = _load_lock_map(vault_file)
    return locks.get(environment)


def list_locked_environments(vault_file: str) -> dict:
    """Return a mapping of all locked environments to their lock info."""
    return _load_lock_map(vault_file)


class EnvironmentLockedError(RuntimeError):
    """Raised when a write is attempted on a locked environment."""
