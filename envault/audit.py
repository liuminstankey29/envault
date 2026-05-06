"""Audit log for envault — records secret access and mutation events."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AUDIT_LOG_ENV_VAR = "ENVAULT_AUDIT_LOG"
DEFAULT_AUDIT_LOG = ".envault_audit.jsonl"


def _audit_log_path(log_path: Optional[str] = None) -> Path:
    """Return the path to the audit log file."""
    if log_path:
        return Path(log_path)
    return Path(os.environ.get(AUDIT_LOG_ENV_VAR, DEFAULT_AUDIT_LOG))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_event(
    action: str,
    environment: str,
    key: Optional[str] = None,
    extra: Optional[dict] = None,
    log_path: Optional[str] = None,
) -> dict:
    """Append a single audit event to the JSONL log and return the event dict."""
    event = {
        "timestamp": _now_iso(),
        "action": action,
        "environment": environment,
    }
    if key is not None:
        event["key"] = key
    if extra:
        event.update(extra)

    path = _audit_log_path(log_path)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
    return event


def read_events(log_path: Optional[str] = None) -> list:
    """Read all audit events from the log; return empty list if absent."""
    path = _audit_log_path(log_path)
    if not path.exists():
        return []
    events = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def filter_events(
    events: list,
    action: Optional[str] = None,
    environment: Optional[str] = None,
    key: Optional[str] = None,
) -> list:
    """Filter a list of events by optional action, environment, or key."""
    result = events
    if action:
        result = [e for e in result if e.get("action") == action]
    if environment:
        result = [e for e in result if e.get("environment") == environment]
    if key:
        result = [e for e in result if e.get("key") == key]
    return result
