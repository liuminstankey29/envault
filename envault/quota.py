"""Per-environment secret quota enforcement."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envault.vault import read_secrets


def _quota_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".quota.json")


def _load_quota_map(vault_path: str) -> dict:
    p = _quota_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_quota_map(vault_path: str, data: dict) -> None:
    _quota_path(vault_path).write_text(json.dumps(data, indent=2))


@dataclass
class QuotaStatus:
    environment: str
    limit: Optional[int]
    used: int

    @property
    def available(self) -> Optional[int]:
        if self.limit is None:
            return None
        return max(0, self.limit - self.used)

    @property
    def exceeded(self) -> bool:
        if self.limit is None:
            return False
        return self.used > self.limit


def set_quota(vault_path: str, environment: str, limit: int) -> None:
    """Set the maximum number of secrets allowed in *environment*."""
    if limit < 1:
        raise ValueError("Quota limit must be a positive integer.")
    data = _load_quota_map(vault_path)
    data[environment] = limit
    _save_quota_map(vault_path, data)


def remove_quota(vault_path: str, environment: str) -> bool:
    """Remove the quota for *environment*. Returns True if one existed."""
    data = _load_quota_map(vault_path)
    if environment not in data:
        return False
    del data[environment]
    _save_quota_map(vault_path, data)
    return True


def get_quota_status(vault_path: str, environment: str, password: str) -> QuotaStatus:
    """Return current quota usage for *environment*."""
    data = _load_quota_map(vault_path)
    limit = data.get(environment)
    try:
        secrets = read_secrets(vault_path, environment, password)
        used = len(secrets)
    except Exception:
        used = 0
    return QuotaStatus(environment=environment, limit=limit, used=used)


def check_quota(vault_path: str, environment: str, password: str) -> QuotaStatus:
    """Raise RuntimeError if the quota for *environment* is exceeded."""
    status = get_quota_status(vault_path, environment, password)
    if status.exceeded:
        raise RuntimeError(
            f"Quota exceeded for '{environment}': "
            f"{status.used}/{status.limit} secrets."
        )
    return status


def list_quotas(vault_path: str) -> dict[str, int]:
    """Return a mapping of environment -> limit for all configured quotas."""
    return dict(_load_quota_map(vault_path))
