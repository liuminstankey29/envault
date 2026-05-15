"""Label management for vault environments and secrets."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


def _label_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".labels.json")


def _load_label_map(vault_path: str) -> Dict[str, Dict[str, List[str]]]:
    """Returns {env: {key: [label, ...]}}."""
    p = _label_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_label_map(vault_path: str, data: Dict[str, Dict[str, List[str]]]) -> None:
    _label_path(vault_path).write_text(json.dumps(data, indent=2))


@dataclass
class LabelResult:
    environment: str
    key: str
    label: str
    added: bool  # False means it was already present / already removed


def add_label(vault_path: str, environment: str, key: str, label: str) -> LabelResult:
    """Attach *label* to *key* in *environment*. Idempotent."""
    data = _load_label_map(vault_path)
    env_map = data.setdefault(environment, {})
    labels = env_map.setdefault(key, [])
    if label in labels:
        return LabelResult(environment=environment, key=key, label=label, added=False)
    labels.append(label)
    _save_label_map(vault_path, data)
    return LabelResult(environment=environment, key=key, label=label, added=True)


def remove_label(vault_path: str, environment: str, key: str, label: str) -> LabelResult:
    """Remove *label* from *key* in *environment*. Returns added=False when not present."""
    data = _load_label_map(vault_path)
    labels: List[str] = data.get(environment, {}).get(key, [])
    if label not in labels:
        return LabelResult(environment=environment, key=key, label=label, added=False)
    labels.remove(label)
    data[environment][key] = labels
    _save_label_map(vault_path, data)
    return LabelResult(environment=environment, key=key, label=label, added=True)


def list_labels(vault_path: str, environment: str, key: Optional[str] = None) -> Dict[str, List[str]]:
    """Return label mapping for *environment*. Optionally filter to a single *key*."""
    data = _load_label_map(vault_path)
    env_map = data.get(environment, {})
    if key is not None:
        return {key: env_map.get(key, [])}
    return {k: v for k, v in env_map.items() if v}


def filter_by_label(vault_path: str, environment: str, label: str) -> List[str]:
    """Return all keys in *environment* that carry *label*."""
    env_map = _load_label_map(vault_path).get(environment, {})
    return [k for k, labels in env_map.items() if label in labels]
