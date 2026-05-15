"""CLI sub-command: envault gc"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.gc import gc_sidecar_files


def cmd_gc(args: argparse.Namespace) -> None:
    vault_path = Path(args.vault)
    password = args.password
    dry_run: bool = getattr(args, "dry_run", False)

    if not vault_path.exists():
        print(f"error: vault not found: {vault_path}", file=sys.stderr)
        sys.exit(1)

    result = gc_sidecar_files(vault_path, password, dry_run=dry_run)

    if result.total_removed == 0:
        print("gc: nothing to clean up.")
        return

    mode = "[dry-run] " if dry_run else ""
    print(f"{mode}gc: removed {result.total_removed} orphaned entr"
          f"{'y' if result.total_removed == 1 else 'ies'} "
          f"across {result.total_files_cleaned} sidecar file"
          f"{'s' if result.total_files_cleaned != 1 else ''}.")

    if getattr(args, "verbose", False):
        for key in result.removed_keys:
            print(f"  - {key}")


def register_gc_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "gc",
        help="Remove orphaned sidecar data for deleted environments",
    )
    p.add_argument("vault", help="Path to the vault file")
    p.add_argument("--password", required=True, help="Master vault password")
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Report what would be removed without modifying files",
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="List every removed entry",
    )
    p.set_defaults(func=cmd_gc)
