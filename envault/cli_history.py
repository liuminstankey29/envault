"""CLI sub-commands for secret history."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict

from envault.history import read_history, format_history


def cmd_history(args) -> None:
    entries = read_history(
        vault_path=args.vault,
        environment=getattr(args, "env", None),
        key=getattr(args, "key", None),
        action=getattr(args, "action", None),
        limit=getattr(args, "limit", None),
    )

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(json.dumps([asdict(e) for e in entries], indent=2))
    else:
        print(format_history(entries))

    if not entries:
        sys.exit(0)


def register_history_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "history",
        help="Show change history for secrets",
    )
    p.add_argument("vault", help="Path to the vault file")
    p.add_argument("--env", default=None, help="Filter by environment")
    p.add_argument("--key", default=None, help="Filter by secret key")
    p.add_argument(
        "--action",
        default=None,
        choices=["set", "delete", "rotate"],
        help="Filter by action type",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Show only the last N entries",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_history)
