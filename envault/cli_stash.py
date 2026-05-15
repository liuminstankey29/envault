"""CLI commands for the secret stash feature."""
from __future__ import annotations

import json
import sys
from typing import Any

from envault.stash import stash_list, stash_pop, stash_push, stash_show
from envault.vault import read_secrets, write_secrets


def cmd_stash(args: Any) -> None:
    sub = args.stash_cmd

    if sub == "push":
        try:
            secrets = read_secrets(args.vault, args.env, args.password)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        result = stash_push(args.vault, args.env, secrets, name=args.name)
        print(f"Stashed {result.count} secret(s) into '{args.env}/{args.name}'.")

    elif sub == "pop":
        secrets = stash_pop(args.vault, args.env, name=args.name)
        if secrets is None:
            print(
                f"error: no stash '{args.env}/{args.name}' found.",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            write_secrets(args.vault, args.env, args.password, secrets)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(
            f"Popped {len(secrets)} secret(s) from '{args.env}/{args.name}' "
            f"back into vault."
        )

    elif sub == "show":
        secrets = stash_show(args.vault, args.env, name=args.name)
        if secrets is None:
            print(
                f"error: no stash '{args.env}/{args.name}' found.",
                file=sys.stderr,
            )
            sys.exit(1)
        if getattr(args, "format", "text") == "json":
            print(json.dumps(secrets, indent=2))
        else:
            for k, v in secrets.items():
                print(f"{k}={v}")

    elif sub == "list":
        slots = stash_list(args.vault, environment=getattr(args, "env", None))
        if not slots:
            print("No stash slots found.")
        else:
            for slot in slots:
                print(slot)

    else:
        print(f"Unknown stash sub-command: {sub}", file=sys.stderr)
        sys.exit(1)


def register_stash_parser(subparsers: Any) -> None:
    p = subparsers.add_parser("stash", help="Temporarily stash secrets aside")
    p.add_argument("--vault", required=True)
    sub = p.add_subparsers(dest="stash_cmd", required=True)

    push = sub.add_parser("push", help="Push current env secrets into a stash slot")
    push.add_argument("--env", required=True)
    push.add_argument("--password", required=True)
    push.add_argument("--name", default="default")

    pop = sub.add_parser("pop", help="Pop stash slot back into the vault")
    pop.add_argument("--env", required=True)
    pop.add_argument("--password", required=True)
    pop.add_argument("--name", default="default")

    show = sub.add_parser("show", help="Show contents of a stash slot")
    show.add_argument("--env", required=True)
    show.add_argument("--name", default="default")
    show.add_argument("--format", choices=["text", "json"], default="text")

    lst = sub.add_parser("list", help="List all stash slots")
    lst.add_argument("--env", default=None)

    p.set_defaults(func=cmd_stash)
