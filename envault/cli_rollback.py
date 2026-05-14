"""CLI commands for rolling back an environment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.rollback import rollback_to_snapshot, rollback_to_history
from envault.snapshot import list_snapshots


def cmd_rollback(args: argparse.Namespace) -> None:
    vault_path = Path(args.vault)

    if args.snapshot:
        try:
            result = rollback_to_snapshot(
                vault_path,
                environment=args.environment,
                password=args.password,
                snapshot_name=args.snapshot,
            )
        except (FileNotFoundError, KeyError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

        print(
            f"Rolled back '{result.environment}' to snapshot '{result.label}' "
            f"({result.keys_restored} key(s) restored, was {result.previous_keys})."
        )

    elif args.steps is not None:
        result = rollback_to_history(
            vault_path,
            environment=args.environment,
            password=args.password,
            steps=args.steps,
        )
        if result is None:
            print(
                f"error: not enough history to roll back {args.steps} step(s).",
                file=sys.stderr,
            )
            sys.exit(1)

        print(
            f"Rolled back '{result.environment}' {args.steps} history step(s) "
            f"(restored {result.keys_restored} key(s), was {result.previous_keys})."
        )

    elif args.list_snapshots:
        snapshots = list_snapshots(vault_path, args.environment)
        if not snapshots:
            print(f"No snapshots found for environment '{args.environment}'.")
        else:
            print(f"Snapshots for '{args.environment}':")
            for snap in snapshots:
                print(f"  {snap['name']}  ({snap['created_at']})")
    else:
        print("error: specify --snapshot, --steps, or --list-snapshots.", file=sys.stderr)
        sys.exit(1)


def register_rollback_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("rollback", help="Roll back an environment to a previous state")
    p.add_argument("vault", help="Path to the vault file")
    p.add_argument("environment", help="Environment name")
    p.add_argument("--password", required=True, help="Master password")
    p.add_argument("--snapshot", metavar="NAME", help="Restore to this snapshot name")
    p.add_argument(
        "--steps",
        type=int,
        metavar="N",
        help="Roll back N history steps",
    )
    p.add_argument(
        "--list-snapshots",
        action="store_true",
        help="List available snapshots for the environment",
    )
    p.set_defaults(func=cmd_rollback)
