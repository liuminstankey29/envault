"""Temporary secret stash — save secrets aside without writing to the vault."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


def _stash_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".stash.json")


def _load_stash(vault_path: str) -> Dict[str, Dict[str, str]]:
    p = _stash_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_stash(vault_path: str, data: Dict[str, Dict[str, str]]) -> None:
    _stash_path(vault_path).write_text(json.dumps(data, indent=2))


@dataclass
class StashResult:
    stash_name: str
    keys: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.keys)


def stash_push(
    vault_path: str,
    environment: str,
    secrets: Dict[str, str],
    name: str = "default",
) -> StashResult:
    """Push a dict of secrets into a named stash slot."""
    data = _load_stash(vault_path)
    slot_key = f"{environment}/{name}"
    data[slot_key] = dict(secrets)
    _save_stash(vault_path, data)
    return StashResult(stash_name=name, keys=list(secrets.keys()))


def stash_pop(
    vault_path: str,
    environment: str,
    name: str = "default",
) -> Optional[Dict[str, str]]:
    """Pop secrets from a named stash slot, removing it."""
    data = _load_stash(vault_path)
    slot_key = f"{environment}/{name}"
    secrets = data.pop(slot_key, None)
    if secrets is not None:
        _save_stash(vault_path, data)
    return secrets


def stash_list(vault_path: str, environment: Optional[str] = None) -> List[str]:
    """List stash slot names, optionally filtered by environment."""
    data = _load_stash(vault_path)
    names = []
    for slot_key in data:
        env, _, name = slot_key.partition("/")
        if environment is None or env == environment:
            names.append(slot_key)
    return sorted(names)


def stash_show(
    vault_path: str,
    environment: str,
    name: str = "default",
) -> Optional[Dict[str, str]]:
    """Peek at a stash slot without removing it."""
    data = _load_stash(vault_path)
    slot_key = f"{environment}/{name}"
    return data.get(slot_key)
