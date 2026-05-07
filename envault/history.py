"""Secret change history tracking for envault."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


def _history_path(vault_path: str) -> Path:
    p = Path(vault_path)
    return p.parent / (p.stem + ".history.json")


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class HistoryEntry:
    timestamp: str
    environment: str
    key: str
    action: str          # "set", "delete", "rotate"
    actor: Optional[str] = None


def record_change(
    vault_path: str,
    environment: str,
    key: str,
    action: str,
    actor: Optional[str] = None,
) -> HistoryEntry:
    """Append a change record to the history log."""
    entry = HistoryEntry(
        timestamp=_now_iso(),
        environment=environment,
        key=key,
        action=action,
        actor=actor,
    )
    path = _history_path(vault_path)
    records: list = []
    if path.exists():
        records = json.loads(path.read_text())
    records.append(asdict(entry))
    path.write_text(json.dumps(records, indent=2))
    return entry


def read_history(
    vault_path: str,
    environment: Optional[str] = None,
    key: Optional[str] = None,
    action: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[HistoryEntry]:
    """Return history entries, optionally filtered."""
    path = _history_path(vault_path)
    if not path.exists():
        return []
    records = json.loads(path.read_text())
    entries = [HistoryEntry(**r) for r in records]
    if environment:
        entries = [e for e in entries if e.environment == environment]
    if key:
        entries = [e for e in entries if e.key == key]
    if action:
        entries = [e for e in entries if e.action == action]
    if limit is not None:
        entries = entries[-limit:]
    return entries


def format_history(entries: List[HistoryEntry]) -> str:
    """Return a human-readable table of history entries."""
    if not entries:
        return "(no history)"
    lines = [f"{'TIMESTAMP':<22} {'ENV':<14} {'KEY':<20} {'ACTION':<8} ACTOR"]
    lines.append("-" * 74)
    for e in entries:
        actor = e.actor or "-"
        lines.append(f"{e.timestamp:<22} {e.environment:<14} {e.key:<20} {e.action:<8} {actor}")
    return "\n".join(lines)
