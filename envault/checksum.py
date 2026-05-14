"""Checksum utilities: compute and verify per-environment secret checksums."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from envault.vault import read_secrets


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _checksum_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".checksums.json")


def _load_checksum_map(vault_path: str) -> Dict[str, str]:
    p = _checksum_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_checksum_map(vault_path: str, data: Dict[str, str]) -> None:
    _checksum_path(vault_path).write_text(json.dumps(data, indent=2))


def _compute_checksum(secrets: Dict[str, str]) -> str:
    """Return a SHA-256 hex digest of the canonical JSON representation."""
    canonical = json.dumps(secrets, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class ChecksumResult:
    environment: str
    checksum: str
    stored: Optional[str]
    matched: bool


def compute_and_store(vault_path: str, environment: str, password: str) -> str:
    """Compute the checksum for *environment* and persist it; return the hex digest."""
    secrets = read_secrets(vault_path, environment, password)
    digest = _compute_checksum(secrets)
    data = _load_checksum_map(vault_path)
    data[environment] = digest
    _save_checksum_map(vault_path, data)
    return digest


def verify_checksum(vault_path: str, environment: str, password: str) -> ChecksumResult:
    """Verify the current secrets against the stored checksum."""
    secrets = read_secrets(vault_path, environment, password)
    current = _compute_checksum(secrets)
    stored = _load_checksum_map(vault_path).get(environment)
    return ChecksumResult(
        environment=environment,
        checksum=current,
        stored=stored,
        matched=(stored == current),
    )


def list_checksums(vault_path: str) -> Dict[str, str]:
    """Return all stored environment → checksum mappings."""
    return dict(_load_checksum_map(vault_path))


def clear_checksum(vault_path: str, environment: str) -> bool:
    """Remove the stored checksum for *environment*. Returns True if one existed."""
    data = _load_checksum_map(vault_path)
    if environment not in data:
        return False
    del data[environment]
    _save_checksum_map(vault_path, data)
    return True
