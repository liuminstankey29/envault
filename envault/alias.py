"""Environment alias support — map short names to full environment names."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


def _alias_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".aliases.json")


def _load_alias_map(vault_path: str) -> Dict[str, str]:
    p = _alias_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_alias_map(vault_path: str, alias_map: Dict[str, str]) -> None:
    _alias_path(vault_path).write_text(json.dumps(alias_map, indent=2))


def set_alias(vault_path: str, alias: str, environment: str) -> bool:
    """Create or update an alias. Returns True if newly created, False if updated."""
    alias_map = _load_alias_map(vault_path)
    is_new = alias not in alias_map
    alias_map[alias] = environment
    _save_alias_map(vault_path, alias_map)
    return is_new


def remove_alias(vault_path: str, alias: str) -> bool:
    """Remove an alias. Returns True if it existed, False otherwise."""
    alias_map = _load_alias_map(vault_path)
    if alias not in alias_map:
        return False
    del alias_map[alias]
    _save_alias_map(vault_path, alias_map)
    return True


def resolve_alias(vault_path: str, name: str) -> str:
    """Resolve a name through aliases. Returns the target env name (or name itself)."""
    alias_map = _load_alias_map(vault_path)
    return alias_map.get(name, name)


def list_aliases(vault_path: str) -> Dict[str, str]:
    """Return all aliases as {alias: environment} mapping."""
    return _load_alias_map(vault_path)


def get_alias_target(vault_path: str, alias: str) -> Optional[str]:
    """Return the target environment for the given alias, or None if not found."""
    return _load_alias_map(vault_path).get(alias)
