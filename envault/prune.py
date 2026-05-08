"""Remove secrets that have expired TTLs or match a given filter from an environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.vault import read_secrets, write_secrets
from envault.ttl import get_expiry, clear_expiry, _load_ttl_map, _save_ttl_map, _ttl_path
from envault.history import record_change


@dataclass
class PruneResult:
    removed: List[str] = field(default_factory=list)
    kept: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed)

    @property
    def total_kept(self) -> int:
        return len(self.kept)


def prune_expired(
    vault_path: str,
    environment: str,
    password: str,
    *,
    dry_run: bool = False,
) -> PruneResult:
    """Remove all secrets whose TTL has expired from *environment*."""
    from datetime import datetime, timezone

    secrets = read_secrets(vault_path, environment, password)
    result = PruneResult()
    now = datetime.now(timezone.utc)

    to_keep = {}
    for key, value in secrets.items():
        expiry = get_expiry(vault_path, environment, key)
        if expiry is not None and expiry <= now:
            result.removed.append(key)
            if not dry_run:
                clear_expiry(vault_path, environment, key)
                record_change(vault_path, environment, key, "prune", actor="envault")
        else:
            result.kept.append(key)
            to_keep[key] = value

    if not dry_run and result.removed:
        write_secrets(vault_path, environment, password, to_keep)

    return result


def prune_keys(
    vault_path: str,
    environment: str,
    password: str,
    keys: List[str],
    *,
    dry_run: bool = False,
) -> PruneResult:
    """Remove a specific list of *keys* from *environment*."""
    secrets = read_secrets(vault_path, environment, password)
    result = PruneResult()

    to_keep = {}
    for key, value in secrets.items():
        if key in keys:
            result.removed.append(key)
            if not dry_run:
                clear_expiry(vault_path, environment, key)
                record_change(vault_path, environment, key, "prune", actor="envault")
        else:
            result.kept.append(key)
            to_keep[key] = value

    if not dry_run and result.removed:
        write_secrets(vault_path, environment, password, to_keep)

    return result
