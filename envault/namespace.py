"""Namespace support: group secrets under logical prefixes within an environment."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import read_secrets, write_secrets


def _namespace_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".namespaces.json")


def _load_namespace_map(vault_path: str) -> Dict[str, str]:
    """Return {key: namespace} mapping."""
    p = _namespace_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_namespace_map(vault_path: str, mapping: Dict[str, str]) -> None:
    _namespace_path(vault_path).write_text(json.dumps(mapping, indent=2))


@dataclass
class NamespaceResult:
    namespace: str
    keys_affected: List[str] = field(default_factory=list)
    already_assigned: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.keys_affected)


def assign_namespace(
    vault_path: str,
    env: str,
    password: str,
    namespace: str,
    keys: List[str],
    overwrite: bool = False,
) -> NamespaceResult:
    """Assign keys to a namespace. Skips already-assigned keys unless overwrite=True."""
    secrets = read_secrets(vault_path, env, password)
    mapping = _load_namespace_map(vault_path)
    ns_key = f"{env}::{{}}".format

    result = NamespaceResult(namespace=namespace)
    for k in keys:
        if k not in secrets:
            continue
        full_key = f"{env}::{k}"
        if full_key in mapping and not overwrite:
            result.already_assigned.append(k)
        else:
            mapping[full_key] = namespace
            result.keys_affected.append(k)

    _save_namespace_map(vault_path, mapping)
    return result


def get_namespace(vault_path: str, env: str, key: str) -> Optional[str]:
    """Return the namespace for a given env+key, or None."""
    mapping = _load_namespace_map(vault_path)
    return mapping.get(f"{env}::{key}")


def list_namespace_keys(
    vault_path: str, env: str, password: str, namespace: str
) -> Dict[str, str]:
    """Return {key: value} for all keys in the given namespace."""
    secrets = read_secrets(vault_path, env, password)
    mapping = _load_namespace_map(vault_path)
    return {
        k: v
        for k, v in secrets.items()
        if mapping.get(f"{env}::{k}") == namespace
    }


def remove_namespace(vault_path: str, env: str, keys: List[str]) -> List[str]:
    """Remove namespace assignment for the given keys. Returns list of cleared keys."""
    mapping = _load_namespace_map(vault_path)
    cleared = []
    for k in keys:
        full_key = f"{env}::{k}"
        if full_key in mapping:
            del mapping[full_key]
            cleared.append(k)
    _save_namespace_map(vault_path, mapping)
    return cleared
