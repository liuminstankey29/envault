"""Per-environment access control: define which keys are readable/writable per role."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


def _access_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".access.json")


def _load_access_map(vault_path: str) -> dict:
    p = _access_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_access_map(vault_path: str, data: dict) -> None:
    _access_path(vault_path).write_text(json.dumps(data, indent=2))


@dataclass
class AccessRule:
    role: str
    environment: str
    readable_keys: List[str] = field(default_factory=list)  # empty = all
    writable_keys: List[str] = field(default_factory=list)  # empty = none


def set_access_rule(vault_path: str, rule: AccessRule) -> None:
    """Persist an access rule for a role/environment pair."""
    data = _load_access_map(vault_path)
    env_rules = data.setdefault(rule.environment, {})
    env_rules[rule.role] = {
        "readable_keys": rule.readable_keys,
        "writable_keys": rule.writable_keys,
    }
    _save_access_map(vault_path, data)


def get_access_rule(vault_path: str, environment: str, role: str) -> Optional[AccessRule]:
    """Return the access rule for a role in an environment, or None."""
    data = _load_access_map(vault_path)
    entry = data.get(environment, {}).get(role)
    if entry is None:
        return None
    return AccessRule(
        role=role,
        environment=environment,
        readable_keys=entry.get("readable_keys", []),
        writable_keys=entry.get("writable_keys", []),
    )


def remove_access_rule(vault_path: str, environment: str, role: str) -> bool:
    """Remove a rule. Returns True if it existed."""
    data = _load_access_map(vault_path)
    removed = data.get(environment, {}).pop(role, None)
    if removed is not None:
        _save_access_map(vault_path, data)
        return True
    return False


def list_access_rules(vault_path: str, environment: Optional[str] = None) -> List[AccessRule]:
    """List all access rules, optionally filtered by environment."""
    data = _load_access_map(vault_path)
    rules: List[AccessRule] = []
    for env, roles in data.items():
        if environment and env != environment:
            continue
        for role, entry in roles.items():
            rules.append(AccessRule(
                role=role,
                environment=env,
                readable_keys=entry.get("readable_keys", []),
                writable_keys=entry.get("writable_keys", []),
            ))
    return rules


def can_read(vault_path: str, environment: str, role: str, key: str) -> bool:
    """Return True if the role may read the given key."""
    rule = get_access_rule(vault_path, environment, role)
    if rule is None:
        return False
    return (not rule.readable_keys) or (key in rule.readable_keys)


def can_write(vault_path: str, environment: str, role: str, key: str) -> bool:
    """Return True if the role may write the given key."""
    rule = get_access_rule(vault_path, environment, role)
    if rule is None:
        return False
    return key in rule.writable_keys
