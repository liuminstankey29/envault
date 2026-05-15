"""CLI commands for namespace management."""
from __future__ import annotations

import sys
from typing import List

from envault.namespace import (
    assign_namespace,
    get_namespace,
    list_namespace_keys,
    remove_namespace,
)


def cmd_namespace(args) -> None:
    sub = args.namespace_cmd

    if sub == "assign":
        result = assign_namespace(
            vault_path=args.vault,
            env=args.env,
            password=args.password,
            namespace=args.namespace,
            keys=args.keys,
            overwrite=getattr(args, "overwrite", False),
        )
        print(f"Namespace '{result.namespace}': assigned {result.total} key(s).")
        if result.already_assigned:
            print(
                f"  Skipped (already assigned): {', '.join(result.already_assigned)}"
            )

    elif sub == "get":
        ns = get_namespace(args.vault, args.env, args.key)
        if ns is None:
            print(f"Key '{args.key}' has no namespace assigned.")
        else:
            print(ns)

    elif sub == "list":
        secrets = list_namespace_keys(
            args.vault, args.env, args.password, args.namespace
        )
        if not secrets:
            print(f"No keys found in namespace '{args.namespace}'.")
            return
        for k, v in sorted(secrets.items()):
            print(f"{k}={v}")

    elif sub == "remove":
        cleared = remove_namespace(args.vault, args.env, args.keys)
        print(f"Cleared namespace for {len(cleared)} key(s): {', '.join(cleared)}")
        missing = [k for k in args.keys if k not in cleared]
        if missing:
            print(f"  Not assigned: {', '.join(missing)}")

    else:
        print(f"Unknown namespace sub-command: {sub}", file=sys.stderr)
        sys.exit(1)


def register_namespace_parser(subparsers) -> None:
    p = subparsers.add_parser("namespace", help="Manage secret namespaces")
    p.add_argument("--vault", required=True)
    sp = p.add_subparsers(dest="namespace_cmd", required=True)

    pa = sp.add_parser("assign", help="Assign keys to a namespace")
    pa.add_argument("--env", required=True)
    pa.add_argument("--password", required=True)
    pa.add_argument("--namespace", required=True)
    pa.add_argument("keys", nargs="+")
    pa.add_argument("--overwrite", action="store_true", default=False)

    pg = sp.add_parser("get", help="Get namespace for a key")
    pg.add_argument("--env", required=True)
    pg.add_argument("--key", required=True)

    pl = sp.add_parser("list", help="List keys in a namespace")
    pl.add_argument("--env", required=True)
    pl.add_argument("--password", required=True)
    pl.add_argument("--namespace", required=True)

    pr = sp.add_parser("remove", help="Remove namespace assignment from keys")
    pr.add_argument("--env", required=True)
    pr.add_argument("keys", nargs="+")

    p.set_defaults(func=cmd_namespace)
