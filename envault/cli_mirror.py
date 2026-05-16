"""CLI sub-command: envault mirror."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from envault.mirror import mirror_environment


def cmd_mirror(args) -> None:
    src_vault = Path(args.src_vault)
    dest_vault = Path(args.dest_vault)

    if not src_vault.exists():
        print(f"error: source vault not found: {src_vault}", file=sys.stderr)
        sys.exit(1)

    keys = args.keys if args.keys else None

    try:
        result = mirror_environment(
            src_vault=src_vault,
            src_password=args.src_password,
            dest_vault=dest_vault,
            dest_password=args.dest_password,
            environment=args.environment,
            keys=keys,
            overwrite=args.overwrite,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Mirror [{result.environment}]  {result.source_vault}  →  {result.dest_vault}")
    print(f"  copied    : {len(result.copied)}")
    if result.overwritten:
        print(f"  overwritten: {len(result.overwritten)}")
    if result.skipped:
        print(f"  skipped   : {len(result.skipped)}  (use --overwrite to replace)")


def register_mirror_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "mirror",
        help="Copy secrets from one vault to another vault.",
    )
    p.add_argument("environment", help="Environment to mirror.")
    p.add_argument("src_vault", help="Path to the source vault file.")
    p.add_argument("dest_vault", help="Path to the destination vault file.")
    p.add_argument("--src-password", required=True, dest="src_password",
                   help="Password for the source vault.")
    p.add_argument("--dest-password", required=True, dest="dest_password",
                   help="Password for the destination vault.")
    p.add_argument("--keys", nargs="+", default=None,
                   help="Limit mirroring to these keys.")
    p.add_argument("--overwrite", action="store_true",
                   help="Overwrite existing keys in the destination.")
    p.set_defaults(func=cmd_mirror)
