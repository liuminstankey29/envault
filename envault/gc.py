"""Garbage collection: remove orphaned sidecar files for deleted environments."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.vault import list_environments

# Sidecar file suffixes that live alongside the vault and are keyed by environment
_SIDECAR_SUFFIXES = [
    ".ttl.json",
    ".lock.json",
    ".tags.json",
    ".audit.jsonl",
    ".history.jsonl",
    ".baseline.json",
    ".checksum.json",
    ".quota.json",
    ".access.json",
    ".policy.json",
    ".sigs.json",
    ".pins.json",
    ".alias.json",
    ".deps.json",
]


@dataclass
class GCResult:
    removed_keys: List[str] = field(default_factory=list)
    sidecar_files_cleaned: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed_keys)

    @property
    def total_files_cleaned(self) -> int:
        return len(self.sidecar_files_cleaned)


def _live_environments(vault_path: Path, password: str) -> set:
    try:
        return set(list_environments(vault_path, password))
    except Exception:
        return set()


def gc_sidecar_files(vault_path: Path, password: str, dry_run: bool = False) -> GCResult:
    """Scan sidecar JSON/JSONL files and remove entries for environments that no
    longer exist in the vault."""
    result = GCResult()
    live_envs = _live_environments(vault_path, password)

    for suffix in _SIDECAR_SUFFIXES:
        sidecar = vault_path.with_suffix(suffix)
        if not sidecar.exists():
            continue

        try:
            if suffix.endswith(".jsonl"):
                lines = sidecar.read_text(encoding="utf-8").splitlines()
                kept, removed = [], []
                for line in lines:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        kept.append(line)
                        continue
                    env = obj.get("environment") or obj.get("env")
                    if env and env not in live_envs:
                        removed.append(f"{sidecar.name}:{env}")
                    else:
                        kept.append(line)
                if removed:
                    result.removed_keys.extend(removed)
                    result.sidecar_files_cleaned.append(sidecar.name)
                    if not dry_run:
                        sidecar.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
            else:
                data = json.loads(sidecar.read_text(encoding="utf-8"))
                dead = [k for k in data if k not in live_envs]
                if dead:
                    for k in dead:
                        result.removed_keys.append(f"{sidecar.name}:{k}")
                        if not dry_run:
                            del data[k]
                    result.sidecar_files_cleaned.append(sidecar.name)
                    if not dry_run:
                        sidecar.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            continue

    return result
