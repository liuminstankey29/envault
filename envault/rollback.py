"""Rollback an environment to a previous snapshot or history entry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envault.snapshot import list_snapshots, restore_snapshot
from envault.history import read_history, record_change
from envault.vault import read_secrets, write_secrets


@dataclass
class RollbackResult:
    environment: str
    source: str          # 'snapshot' or 'history'
    label: str           # snapshot name or history timestamp
    keys_restored: int
    previous_keys: int

    @property
    def total(self) -> int:
        return self.keys_restored


def rollback_to_snapshot(
    vault_path: Path,
    environment: str,
    password: str,
    snapshot_name: str,
) -> RollbackResult:
    """Restore an environment to a named snapshot."""
    previous = read_secrets(vault_path, environment, password)
    keys_before = len(previous)

    restored = restore_snapshot(vault_path, environment, password, snapshot_name)

    record_change(
        vault_path,
        environment=environment,
        action="rollback",
        key="*",
        detail=f"snapshot:{snapshot_name}",
    )

    return RollbackResult(
        environment=environment,
        source="snapshot",
        label=snapshot_name,
        keys_restored=restored,
        previous_keys=keys_before,
    )


def rollback_to_history(
    vault_path: Path,
    environment: str,
    password: str,
    steps: int = 1,
) -> Optional[RollbackResult]:
    """Rollback by replaying history in reverse for `steps` change records.

    Returns None if there is not enough history to roll back.
    """
    entries = read_history(vault_path, environment=environment)
    if not entries:
        return None

    target_entries = entries[: max(0, len(entries) - steps)]
    if not target_entries:
        return None

    previous = read_secrets(vault_path, environment, password)
    keys_before = len(previous)

    # Rebuild state from history: start empty, apply each recorded old_value
    rebuilt: dict[str, str] = {}
    for entry in target_entries:
        if entry.action == "set" and entry.old_value is not None:
            rebuilt[entry.key] = entry.old_value
        elif entry.action == "set" and entry.old_value is None:
            rebuilt.pop(entry.key, None)
        elif entry.action == "delete":
            rebuilt.pop(entry.key, None)

    write_secrets(vault_path, environment, password, rebuilt)

    label = target_entries[-1].timestamp if target_entries else "origin"
    record_change(
        vault_path,
        environment=environment,
        action="rollback",
        key="*",
        detail=f"history:{label}",
    )

    return RollbackResult(
        environment=environment,
        source="history",
        label=label,
        keys_restored=len(rebuilt),
        previous_keys=keys_before,
    )
