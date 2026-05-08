"""Pin management: lock a secret's value to prevent accidental overwrites."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def _pin_path(vault_file: str) -> Path:
    return Path(vault_file).with_suffix(".pins.json")


def _load_pin_map(vault_file: str) -> Dict[str, List[str]]:
    """Return {env: [pinned_key, ...]} mapping."""
    p = _pin_path(vault_file)
    if not p.exists():
        return {}
    with p.open() as fh:
        return json.load(fh)


def _save_pin_map(vault_file: str, pin_map: Dict[str, List[str]]) -> None:
    p = _pin_path(vault_file)
    with p.open("w") as fh:
        json.dump(pin_map, fh, indent=2)


def pin_secret(vault_file: str, environment: str, key: str) -> bool:
    """Pin *key* in *environment*. Returns True if newly pinned, False if already pinned."""
    pin_map = _load_pin_map(vault_file)
    pins = pin_map.setdefault(environment, [])
    if key in pins:
        return False
    pins.append(key)
    _save_pin_map(vault_file, pin_map)
    return True


def unpin_secret(vault_file: str, environment: str, key: str) -> bool:
    """Unpin *key* in *environment*. Returns True if it was pinned, False otherwise."""
    pin_map = _load_pin_map(vault_file)
    pins = pin_map.get(environment, [])
    if key not in pins:
        return False
    pins.remove(key)
    if not pins:
        pin_map.pop(environment, None)
    _save_pin_map(vault_file, pin_map)
    return True


def is_pinned(vault_file: str, environment: str, key: str) -> bool:
    """Return True if *key* is pinned in *environment*."""
    return key in _load_pin_map(vault_file).get(environment, [])


def list_pins(vault_file: str, environment: str) -> List[str]:
    """Return list of pinned keys for *environment*."""
    return list(_load_pin_map(vault_file).get(environment, []))


def assert_not_pinned(vault_file: str, environment: str, key: str) -> None:
    """Raise ValueError if *key* is pinned, preventing a write."""
    if is_pinned(vault_file, environment, key):
        raise ValueError(
            f"Secret '{key}' in environment '{environment}' is pinned and cannot be overwritten. "
            "Unpin it first with 'envault pin unpin'."
        )
