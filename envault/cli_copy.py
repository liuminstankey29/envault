"""CLI commands for copying secrets between environments."""

from __future__ import annotations

import argparse
import sys

from envault.copy import copy_secrets
from envault.audit import record_event


def cmd_copy(args: argparse.Namespace) -> None:
    """Handle the ``copy`` sub-command."""
    keys = args.keys if args.keys else None

    try:
        result = copy_secrets(
            vault_path=args.vault,
            src_env=args.src_env,
            dst_env=args.dst_env,
            src_password=args.src_password,
            dst_password=args.dst_password,
            keys=keys,
            overwrite=not args.no_overwrite,
        )
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)

    record_event(
        "copy",
        environment=f"{args.src_env} -> {args.dst_env}",
        vault=args.vault,
        copied=result["copied"],
        skipped=result["skipped"],
    )

    print(
        f"Copied {result['copied']} secret(s) from '{args.src_env}' "
        f"to '{args.dst_env}' ({result['skipped']} skipped)."
    )


def register_copy_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach the ``copy`` sub-command to *subparsers*."""
    p = subparsers.add_parser(
        "copy",
        help="Copy secrets from one environment to another.",
    )
    p.add_argument("vault", help="Path to the vault file.")
    p.add_argument("src_env", help="Source environment name.")
    p.add_argument("dst_env", help="Destination environment name.")
    p.add_argument("--src-password", required=True, help="Password for the source environment.")
    p.add_argument("--dst-password", required=True, help="Password for the destination environment.")
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        default=[],
        help="Specific keys to copy (copies all if omitted).",
    )
    p.add_argument(
        "--no-overwrite",
        action="store_true",
        default=False,
        help="Skip keys that already exist in the destination environment.",
    )
    p.set_defaults(func=cmd_copy)
