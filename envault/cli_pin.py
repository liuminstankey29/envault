"""CLI commands for pinning/unpinning secrets from rotation."""
from __future__ import annotations

import argparse
import sys

from envault.pin import pin_secret, unpin_secret, is_pinned, list_pinned


def cmd_pin(args) -> None:
    action = args.pin_action

    if action == "add":
        newly = pin_secret(args.vault, args.env, args.key)
        if newly:
            print(f"Pinned '{args.key}' in [{args.env}].")
        else:
            print(f"'{args.key}' in [{args.env}] was already pinned.")

    elif action == "remove":
        was = unpin_secret(args.vault, args.env, args.key)
        if was:
            print(f"Unpinned '{args.key}' in [{args.env}].")
        else:
            print(f"'{args.key}' in [{args.env}] was not pinned.", file=sys.stderr)
            sys.exit(1)

    elif action == "status":
        pinned = is_pinned(args.vault, args.env, args.key)
        state = "pinned" if pinned else "not pinned"
        print(f"'{args.key}' in [{args.env}] is {state}.")

    elif action == "list":
        env_filter = getattr(args, "env", None)
        results = list_pinned(args.vault, env_filter)
        if not results:
            print("No pinned secrets.")
            return
        current_env = None
        for env, key in sorted(results):
            if env != current_env:
                print(f"[{env}]")
                current_env = env
            print(f"  {key}")
    else:
        print(f"Unknown pin action: {action}", file=sys.stderr)
        sys.exit(1)


def register_pin_parser(subparsers) -> None:
    p = subparsers.add_parser("pin", help="Pin or unpin secrets from rotation")
    p.add_argument("--vault", required=True, help="Path to vault file")
    sub = p.add_subparsers(dest="pin_action", required=True)

    add_p = sub.add_parser("add", help="Pin a secret")
    add_p.add_argument("env", help="Environment name")
    add_p.add_argument("key", help="Secret key to pin")

    rm_p = sub.add_parser("remove", help="Unpin a secret")
    rm_p.add_argument("env", help="Environment name")
    rm_p.add_argument("key", help="Secret key to unpin")

    st_p = sub.add_parser("status", help="Check if a secret is pinned")
    st_p.add_argument("env", help="Environment name")
    st_p.add_argument("key", help="Secret key")

    ls_p = sub.add_parser("list", help="List all pinned secrets")
    ls_p.add_argument("--env", default=None, help="Filter by environment")

    p.set_defaults(func=cmd_pin)
