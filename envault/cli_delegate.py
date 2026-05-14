"""CLI commands for delegate token management."""

from __future__ import annotations

import json
import sys
import time
from typing import Any

from envault.delegate import (
    create_delegate,
    list_delegates,
    revoke_delegate,
    validate_delegate,
)


def cmd_delegate(args: Any) -> None:
    sub = args.delegate_cmd

    if sub == "create":
        token = create_delegate(
            vault_path=args.vault,
            environment=args.env,
            access=args.access,
            ttl_seconds=args.ttl,
            label=args.label or "",
        )
        print(f"Delegate token created for [{args.env}] ({args.access}):")
        print(token)
        if args.ttl:
            print(f"Expires in {args.ttl}s")

    elif sub == "revoke":
        removed = revoke_delegate(
            vault_path=args.vault,
            environment=args.env,
            token=args.token,
        )
        if removed:
            print(f"Token revoked from [{args.env}].")
        else:
            print(f"Token not found in [{args.env}].", file=sys.stderr)
            sys.exit(1)

    elif sub == "validate":
        ok = validate_delegate(
            vault_path=args.vault,
            environment=args.env,
            token=args.token,
            required_access=args.access,
        )
        if ok:
            print(f"Token is valid for [{args.env}] ({args.access}).")
        else:
            print(f"Token is INVALID or expired.", file=sys.stderr)
            sys.exit(1)

    elif sub == "list":
        entries = list_delegates(vault_path=args.vault, environment=args.env)
        if not entries:
            print(f"No delegates for [{args.env}].")
            return
        if getattr(args, "format", "text") == "json":
            print(
                json.dumps(
                    [
                        {
                            "token_hash": e.token_hash[:12] + "...",
                            "access": e.access,
                            "expires_at": e.expires_at,
                            "label": e.label,
                        }
                        for e in entries
                    ],
                    indent=2,
                )
            )
        else:
            for e in entries:
                expired = (
                    " [EXPIRED]"
                    if e.expires_at and time.time() > e.expires_at
                    else ""
                )
                label = f" ({e.label})" if e.label else ""
                print(f"  {e.token_hash[:12]}...  access={e.access}{label}{expired}")


def register_delegate_parser(subparsers: Any) -> None:
    p = subparsers.add_parser("delegate", help="Manage delegate access tokens")
    p.add_argument("--vault", required=True)
    sp = p.add_subparsers(dest="delegate_cmd", required=True)

    c = sp.add_parser("create", help="Create a delegate token")
    c.add_argument("--env", required=True)
    c.add_argument("--access", choices=["read", "write"], default="read")
    c.add_argument("--ttl", type=int, default=None, help="Expiry in seconds")
    c.add_argument("--label", default="")

    r = sp.add_parser("revoke", help="Revoke a delegate token")
    r.add_argument("--env", required=True)
    r.add_argument("--token", required=True)

    v = sp.add_parser("validate", help="Check if a token is valid")
    v.add_argument("--env", required=True)
    v.add_argument("--token", required=True)
    v.add_argument("--access", choices=["read", "write"], default="read")

    ls = sp.add_parser("list", help="List delegate tokens for an environment")
    ls.add_argument("--env", required=True)
    ls.add_argument("--format", choices=["text", "json"], default="text")

    p.set_defaults(func=cmd_delegate)
