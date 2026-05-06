"""Diff secrets between two environments or between a file and an environment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .vault import read_secrets


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None


def diff_dicts(
    old: Dict[str, str],
    new: Dict[str, str],
    show_unchanged: bool = False,
) -> List[DiffEntry]:
    """Return a list of DiffEntry objects comparing old and new secret dicts."""
    entries: List[DiffEntry] = []
    all_keys = sorted(set(old) | set(new))

    for key in all_keys:
        if key in old and key not in new:
            entries.append(DiffEntry(key=key, status="removed", old_value=old[key]))
        elif key not in old and key in new:
            entries.append(DiffEntry(key=key, status="added", new_value=new[key]))
        elif old[key] != new[key]:
            entries.append(
                DiffEntry(key=key, status="changed", old_value=old[key], new_value=new[key])
            )
        elif show_unchanged:
            entries.append(
                DiffEntry(key=key, status="unchanged", old_value=old[key], new_value=new[key])
            )

    return entries


def diff_environments(
    vault_path: str,
    env_a: str,
    password_a: str,
    env_b: str,
    password_b: str,
    show_unchanged: bool = False,
) -> List[DiffEntry]:
    """Diff secrets between two named environments in the same vault."""
    secrets_a = read_secrets(vault_path, env_a, password_a)
    secrets_b = read_secrets(vault_path, env_b, password_b)
    return diff_dicts(secrets_a, secrets_b, show_unchanged=show_unchanged)


def format_diff(entries: List[DiffEntry], mask_values: bool = True) -> str:
    """Render diff entries as a human-readable string."""
    if not entries:
        return "(no differences)"

    lines: List[str] = []
    symbols = {"added": "+", "removed": "-", "changed": "~", "unchanged": " "}

    for entry in entries:
        sym = symbols[entry.status]
        if entry.status == "added":
            val = "***" if mask_values else entry.new_value
            lines.append(f"{sym} {entry.key}={val}")
        elif entry.status == "removed":
            val = "***" if mask_values else entry.old_value
            lines.append(f"{sym} {entry.key}={val}")
        elif entry.status == "changed":
            if mask_values:
                lines.append(f"{sym} {entry.key}=*** -> ***")
            else:
                lines.append(f"{sym} {entry.key}={entry.old_value!r} -> {entry.new_value!r}")
        else:
            val = "***" if mask_values else entry.old_value
            lines.append(f"{sym} {entry.key}={val}")

    return "\n".join(lines)
