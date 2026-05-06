"""CLI commands for viewing the envault audit log."""

import argparse
import json
import sys

from envault.audit import read_events, filter_events


def cmd_audit(args) -> None:
    """Display audit log entries, with optional filters."""
    events = read_events(log_path=getattr(args, "log", None))

    events = filter_events(
        events,
        action=getattr(args, "action", None),
        environment=getattr(args, "env", None),
        key=getattr(args, "key", None),
    )

    if not events:
        print("No audit events found.", file=sys.stderr)
        return

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(json.dumps(events, indent=2))
    else:
        for e in events:
            parts = [e.get("timestamp", ""), e.get("action", ""), e.get("environment", "")]
            if "key" in e:
                parts.append(e["key"])
            print("  ".join(parts))


def register_audit_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'audit' sub-command."""
    p = subparsers.add_parser("audit", help="View the audit log")
    p.add_argument("--env", default=None, help="Filter by environment name")
    p.add_argument("--action", default=None, help="Filter by action (set, get, rotate, export)")
    p.add_argument("--key", default=None, help="Filter by secret key")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument("--log", default=None, help="Path to audit log file")
    p.set_defaults(func=cmd_audit)
