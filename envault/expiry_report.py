"""Generate expiry status reports across environments."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from envault.ttl import _load_ttl_map, _now_utc


@dataclass
class ExpiryEntry:
    environment: str
    key: str
    expires_at: str
    is_expired: bool
    days_remaining: Optional[float]


@dataclass
class ExpiryReport:
    entries: List[ExpiryEntry] = field(default_factory=list)

    @property
    def expired(self) -> List[ExpiryEntry]:
        return [e for e in self.entries if e.is_expired]

    @property
    def expiring_soon(self) -> List[ExpiryEntry]:
        return [
            e for e in self.entries
            if not e.is_expired
            and e.days_remaining is not None
            and e.days_remaining <= 7
        ]


def build_expiry_report(
    vault_path: str,
    environments: Optional[List[str]] = None,
) -> ExpiryReport:
    """Build a report of all secrets with TTL metadata."""
    ttl_map = _load_ttl_map(vault_path)
    now = _now_utc()
    report = ExpiryReport()

    for env, keys in ttl_map.items():
        if environments and env not in environments:
            continue
        for key, expires_at_str in keys.items():
            try:
                expires_at = datetime.fromisoformat(expires_at_str).replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue
            is_expired = expires_at <= now
            delta = (expires_at - now).total_seconds() / 86400
            days_remaining = None if is_expired else round(delta, 2)
            report.entries.append(
                ExpiryEntry(
                    environment=env,
                    key=key,
                    expires_at=expires_at_str,
                    is_expired=is_expired,
                    days_remaining=days_remaining,
                )
            )

    return report


def format_expiry_report(report: ExpiryReport, fmt: str = "text") -> str:
    """Render an ExpiryReport as text or JSON."""
    if fmt == "json":
        import json
        return json.dumps(
            [
                {
                    "environment": e.environment,
                    "key": e.key,
                    "expires_at": e.expires_at,
                    "is_expired": e.is_expired,
                    "days_remaining": e.days_remaining,
                }
                for e in report.entries
            ],
            indent=2,
        )

    if not report.entries:
        return "No TTL entries found."

    lines = []
    for e in sorted(report.entries, key=lambda x: (x.environment, x.key)):
        status = "EXPIRED" if e.is_expired else f"{e.days_remaining}d remaining"
        lines.append(f"  [{e.environment}] {e.key}: {e.expires_at} ({status})")
    return "\n".join(lines)
