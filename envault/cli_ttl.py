"""CLI sub-commands for TTL / expiry management."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any

from envault.ttl import (
    clear_expiry,
    get_expiry,
    list_all_expiries,
    list_expired,
    set_expiry,
)


def cmd_ttl(args: Any) -> None:
    sub = args.ttl_cmd

    if sub == "set":
        try:
            expires_at = datetime.fromisoformat(args.expires_at)
        except ValueError:
            print(f"ERROR: invalid datetime '{args.expires_at}'. Use ISO-8601.", file=sys.stderr)
            sys.exit(1)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        set_expiry(args.vault, args.environment, args.key, expires_at)
        print(f"Expiry set for '{args.key}' in [{args.environment}]: {expires_at.isoformat()}")

    elif sub == "clear":
        removed = clear_expiry(args.vault, args.environment, args.key)
        if removed:
            print(f"Expiry cleared for '{args.key}' in [{args.environment}].")
        else:
            print(f"No expiry found for '{args.key}' in [{args.environment}].")

    elif sub == "get":
        exp = get_expiry(args.vault, args.environment, args.key)
        if exp is None:
            print(f"No expiry set for '{args.key}' in [{args.environment}].")
        else:
            now = datetime.now(tz=timezone.utc)
            status = "EXPIRED" if exp <= now else "active"
            print(f"{args.key}: {exp.isoformat()} [{status}]")

    elif sub == "list":
        expiries = list_all_expiries(args.vault, args.environment)
        if not expiries:
            print(f"No expiries set for [{args.environment}].")
            return
        now = datetime.now(tz=timezone.utc)
        for key, exp in sorted(expiries.items()):
            status = "EXPIRED" if exp <= now else "active"
            print(f"  {key}: {exp.isoformat()} [{status}]")

    elif sub == "expired":
        keys = list_expired(args.vault, args.environment)
        if not keys:
            print(f"No expired secrets in [{args.environment}].")
        else:
            print(f"Expired secrets in [{args.environment}]:")
            for k in keys:
                print(f"  {k}")


def register_ttl_parser(subparsers: Any) -> None:
    p = subparsers.add_parser("ttl", help="Manage secret expiry (TTL)")
    p.add_argument("--vault", default="vault.enc", help="Vault file path")
    p.add_argument("--environment", "-e", required=True, help="Environment name")
    sp = p.add_subparsers(dest="ttl_cmd", required=True)

    s = sp.add_parser("set", help="Set expiry for a key")
    s.add_argument("key")
    s.add_argument("expires_at", help="ISO-8601 datetime, e.g. 2025-12-31T23:59:59")

    c = sp.add_parser("clear", help="Remove expiry for a key")
    c.add_argument("key")

    g = sp.add_parser("get", help="Show expiry for a key")
    g.add_argument("key")

    sp.add_parser("list", help="List all expiries for an environment")
    sp.add_parser("expired", help="List expired secrets")

    p.set_defaults(func=cmd_ttl)
