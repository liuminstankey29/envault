"""Environment fingerprinting — compute and compare stable identity hashes for environments."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envault.vault import read_secrets


def _fingerprint_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".fingerprints.json")


def _load_fingerprint_map(vault_path: str) -> dict:
    p = _fingerprint_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_fingerprint_map(vault_path: str, data: dict) -> None:
    _fingerprint_path(vault_path).write_text(json.dumps(data, indent=2))


def _compute_fingerprint(secrets: dict) -> str:
    """Return a stable SHA-256 hex digest of the sorted key-value pairs."""
    canonical = json.dumps(secrets, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class FingerprintResult:
    environment: str
    fingerprint: str
    previous: Optional[str]
    changed: bool


def compute_fingerprint(
    vault_path: str,
    environment: str,
    password: str,
    *,
    store: bool = True,
) -> FingerprintResult:
    """Compute the fingerprint for *environment* and optionally persist it."""
    secrets = read_secrets(vault_path, environment, password)
    fp = _compute_fingerprint(secrets)

    fmap = _load_fingerprint_map(vault_path)
    previous = fmap.get(environment)
    changed = previous != fp

    if store:
        fmap[environment] = fp
        _save_fingerprint_map(vault_path, fmap)

    return FingerprintResult(
        environment=environment,
        fingerprint=fp,
        previous=previous,
        changed=changed,
    )


def get_fingerprint(vault_path: str, environment: str) -> Optional[str]:
    """Return the last stored fingerprint for *environment*, or None."""
    return _load_fingerprint_map(vault_path).get(environment)


def clear_fingerprint(vault_path: str, environment: str) -> bool:
    """Remove the stored fingerprint for *environment*. Returns True if it existed."""
    fmap = _load_fingerprint_map(vault_path)
    if environment not in fmap:
        return False
    del fmap[environment]
    _save_fingerprint_map(vault_path, fmap)
    return True
