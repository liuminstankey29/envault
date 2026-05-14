"""Environment summary report: key counts, expiry status, lock state, tags, and quota."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envault.vault import list_environments, read_secrets
from envault.lock import is_locked
from envault.ttl import list_expiring
from envault.tags import list_tags
from envault.quota import get_quota_status


@dataclass
class EnvironmentSummary:
    environment: str
    key_count: int
    locked: bool
    lock_reason: Optional[str]
    expired_keys: list[str]
    expiring_soon_keys: list[str]
    tagged_keys: int
    quota_limit: Optional[int]
    quota_used: int

    @property
    def quota_pct(self) -> Optional[float]:
        if self.quota_limit:
            return round(100.0 * self.quota_used / self.quota_limit, 1)
        return None


def summarise_environment(
    vault_path: Path,
    environment: str,
    password: str,
    warn_days: int = 7,
) -> EnvironmentSummary:
    secrets = read_secrets(vault_path, environment, password)
    key_count = len(secrets)

    lock_info = is_locked(vault_path, environment)
    locked = lock_info is not None
    lock_reason = lock_info if isinstance(lock_info, str) and lock_info else None

    expiry_entries = list_expiring(vault_path, environment, warn_days=warn_days)
    expired_keys = [e.key for e in expiry_entries if e.is_expired]
    expiring_soon_keys = [e.key for e in expiry_entries if not e.is_expired]

    tags_map = list_tags(vault_path, environment)
    tagged_keys = len(tags_map)

    quota = get_quota_status(vault_path, environment, current_count=key_count)
    quota_limit = quota.limit if quota else None
    quota_used = quota.used if quota else key_count

    return EnvironmentSummary(
        environment=environment,
        key_count=key_count,
        locked=locked,
        lock_reason=lock_reason,
        expired_keys=expired_keys,
        expiring_soon_keys=expiring_soon_keys,
        tagged_keys=tagged_keys,
        quota_limit=quota_limit,
        quota_used=quota_used,
    )


def summarise_all(
    vault_path: Path,
    passwords: dict[str, str],
    warn_days: int = 7,
) -> list[EnvironmentSummary]:
    results = []
    for env in list_environments(vault_path):
        pw = passwords.get(env)
        if pw is None:
            continue
        try:
            results.append(summarise_environment(vault_path, env, pw, warn_days))
        except Exception:
            pass
    return results
