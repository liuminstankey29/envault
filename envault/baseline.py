"""Baseline management: capture and compare environment secrets against a known-good state."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import read_secrets


def _baseline_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".baseline.json")


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass
class BaselineDiff:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not (self.added or self.removed or self.changed)


def capture_baseline(
    vault_path: str, environment: str, password: str
) -> Dict[str, str]:
    """Read current secrets and save their hashes as the baseline."""
    secrets = read_secrets(vault_path, environment, password)
    hashes = {k: _hash_value(v) for k, v in secrets.items()}
    baseline_file = _baseline_path(vault_path)
    try:
        data = json.loads(baseline_file.read_text())
    except FileNotFoundError:
        data = {}
    data[environment] = hashes
    baseline_file.write_text(json.dumps(data, indent=2))
    return hashes


def load_baseline(vault_path: str, environment: str) -> Optional[Dict[str, str]]:
    """Return stored hash map for the environment, or None if not captured."""
    baseline_file = _baseline_path(vault_path)
    try:
        data = json.loads(baseline_file.read_text())
    except FileNotFoundError:
        return None
    return data.get(environment)


def compare_to_baseline(
    vault_path: str, environment: str, password: str
) -> Optional[BaselineDiff]:
    """Compare current secrets against the stored baseline.

    Returns None if no baseline has been captured yet.
    """
    stored = load_baseline(vault_path, environment)
    if stored is None:
        return None
    current = read_secrets(vault_path, environment, password)
    current_hashes = {k: _hash_value(v) for k, v in current.items()}

    diff = BaselineDiff()
    all_keys = set(stored) | set(current_hashes)
    for key in sorted(all_keys):
        if key not in stored:
            diff.added.append(key)
        elif key not in current_hashes:
            diff.removed.append(key)
        elif stored[key] != current_hashes[key]:
            diff.changed.append(key)
        else:
            diff.unchanged.append(key)
    return diff


def clear_baseline(vault_path: str, environment: str) -> bool:
    """Remove the baseline for a specific environment. Returns True if it existed."""
    baseline_file = _baseline_path(vault_path)
    try:
        data = json.loads(baseline_file.read_text())
    except FileNotFoundError:
        return False
    if environment not in data:
        return False
    del data[environment]
    baseline_file.write_text(json.dumps(data, indent=2))
    return True
