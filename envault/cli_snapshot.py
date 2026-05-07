"""CLI commands for snapshot management."""

from __future__ import annotations

import argparse
import json
import sys

from envault.snapshot import (
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)


def cmd_snapshot(args: argparse.Namespace) -> None:
    sub = args.snapshot_cmd

    if sub == "create":
        name = create_snapshot(
            args.vault,
            args.password,
            args.environment,
            args.name or None,
        )
        print(f"Snapshot '{name}' created for environment '{args.environment}'.")

    elif sub == "restore":
        target = getattr(args, "target_environment", None)
        count = restore_snapshot(args.vault, args.password, args.name, target)
        env_label = target or args.name.split("_")[0]
        print(f"Restored {count} secret(s) into environment '{env_label}'.")

    elif sub == "list":
        snapshots = list_snapshots(args.vault)
        if not snapshots:
            print("No snapshots found.")
            return
        if getattr(args, "json", False):
            print(json.dumps(snapshots, indent=2))
        else:
            fmt = "{:<30} {:<15} {:<22} {:>5}"
            print(fmt.format("NAME", "ENVIRONMENT", "CREATED AT", "KEYS"))
            print("-" * 76)
            for s in snapshots:
                print(fmt.format(s["name"], s["environment"], s["created_at"], s["key_count"]))

    elif sub == "delete":
        removed = delete_snapshot(args.vault, args.name)
        if removed:
            print(f"Snapshot '{args.name}' deleted.")
        else:
            print(f"Snapshot '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown snapshot sub-command: {sub}", file=sys.stderr)
        sys.exit(1)


def register_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("snapshot", help="Manage environment snapshots")
    sp = p.add_subparsers(dest="snapshot_cmd", required=True)

    # create
    pc = sp.add_parser("create", help="Create a snapshot of an environment")
    pc.add_argument("environment")
    pc.add_argument("--name", default="", help="Optional snapshot name")

    # restore
    pr = sp.add_parser("restore", help="Restore secrets from a snapshot")
    pr.add_argument("name", help="Snapshot name")
    pr.add_argument("--target-environment", dest="target_environment", default=None)

    # list
    pl = sp.add_parser("list", help="List all snapshots")
    pl.add_argument("--json", action="store_true", help="Output as JSON")

    # delete
    pd = sp.add_parser("delete", help="Delete a snapshot")
    pd.add_argument("name", help="Snapshot name")

    p.set_defaults(func=cmd_snapshot)
