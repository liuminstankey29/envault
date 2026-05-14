"""Secret dependency tracking — define which secrets depend on others."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


def _dep_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".deps.json")


def _load_dep_map(vault_path: str) -> Dict[str, Dict[str, List[str]]]:
    p = _dep_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_dep_map(vault_path: str, data: Dict[str, Dict[str, List[str]]]) -> None:
    _dep_path(vault_path).write_text(json.dumps(data, indent=2))


@dataclass
class DependencyResult:
    environment: str
    key: str
    depends_on: List[str] = field(default_factory=list)
    added: bool = False
    removed: bool = False


def add_dependency(vault_path: str, environment: str, key: str, depends_on: str) -> DependencyResult:
    """Record that *key* depends on *depends_on* within *environment*."""
    data = _load_dep_map(vault_path)
    env_map = data.setdefault(environment, {})
    deps = env_map.setdefault(key, [])
    added = depends_on not in deps
    if added:
        deps.append(depends_on)
    _save_dep_map(vault_path, data)
    return DependencyResult(environment=environment, key=key, depends_on=list(deps), added=added)


def remove_dependency(vault_path: str, environment: str, key: str, depends_on: str) -> DependencyResult:
    """Remove a dependency edge for *key*."""
    data = _load_dep_map(vault_path)
    deps = data.get(environment, {}).get(key, [])
    removed = depends_on in deps
    if removed:
        deps.remove(depends_on)
        data[environment][key] = deps
        _save_dep_map(vault_path, data)
    return DependencyResult(environment=environment, key=key, depends_on=list(deps), removed=removed)


def get_dependencies(vault_path: str, environment: str, key: str) -> List[str]:
    """Return direct dependencies of *key*."""
    return list(_load_dep_map(vault_path).get(environment, {}).get(key, []))


def get_dependents(vault_path: str, environment: str, key: str) -> List[str]:
    """Return keys that directly depend on *key*."""
    env_map = _load_dep_map(vault_path).get(environment, {})
    return [k for k, deps in env_map.items() if key in deps]


def transitive_dependents(vault_path: str, environment: str, key: str) -> Set[str]:
    """Return all keys transitively dependent on *key* (BFS)."""
    visited: Set[str] = set()
    queue = [key]
    while queue:
        current = queue.pop()
        for dep in get_dependents(vault_path, environment, current):
            if dep not in visited:
                visited.add(dep)
                queue.append(dep)
    return visited


def list_all_dependencies(vault_path: str, environment: str) -> Dict[str, List[str]]:
    """Return the full dependency map for *environment*."""
    return dict(_load_dep_map(vault_path).get(environment, {}))
