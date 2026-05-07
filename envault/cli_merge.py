"""CLI sub-commands for merging environments."""

from __future__ import annotations

import argparse
import sys

from envault.merge import merge_environments


def cmd_merge(args: argparse.Namespace) -> None:
    keys = args.keys if args.keys else None
    try:
        result = merge_environments(
            vault_path=args.vault,
            src_env=args.src_env,
            src_password=args.src_password,
            dst_env=args.dst_env,
            dst_password=args.dst_password,
            keys=keys,
            overwrite=args.overwrite,
        )
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)

    if result.added:
        print(f"Added    ({len(result.added)}): {', '.join(sorted(result.added))}")
    if result.overwritten:
        print(f"Replaced ({len(result.overwritten)}): {', '.join(sorted(result.overwritten))}")
    if result.skipped:
        print(f"Skipped  ({len(result.skipped)}): {', '.join(sorted(result.skipped))}")

    total = len(result.added) + len(result.overwritten)
    print(f"\nMerge complete: {total} secret(s) written to '{args.dst_env}'.")


def register_merge_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("merge", help="Merge secrets from one environment into another")
    p.add_argument("src_env", help="Source environment name")
    p.add_argument("dst_env", help="Destination environment name")
    p.add_argument("--src-password", required=True, dest="src_password", help="Password for source environment")
    p.add_argument("--dst-password", required=True, dest="dst_password", help="Password for destination environment")
    p.add_argument("--vault", default="vault.enc", help="Path to vault file (default: vault.enc)")
    p.add_argument("--keys", nargs="+", metavar="KEY", help="Specific keys to merge (default: all)")
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys in destination (default: skip)",
    )
    p.set_defaults(func=cmd_merge)
