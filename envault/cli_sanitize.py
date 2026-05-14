"""CLI commands for the sanitize feature."""
from __future__ import annotations

import argparse
import sys

from envault.sanitize import sanitize_secrets
from envault.vault import read_secrets, write_secrets


def cmd_sanitize(args: argparse.Namespace) -> None:
    """Read secrets for an environment, sanitize them, and write back."""
    try:
        secrets = read_secrets(args.vault, args.env, args.password)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    result = sanitize_secrets(
        secrets,
        strip_whitespace=not args.no_strip,
        strip_quotes=args.strip_quotes,
        warn_placeholders=not args.no_warn_placeholders,
        warn_empty=not args.no_warn_empty,
    )

    if result.warnings:
        for w in result.warnings:
            print(f"  warning: {w}")

    if args.dry_run:
        print(f"dry-run: {len(result.warnings)} issue(s) found, no changes written.")
        sys.exit(1 if result.warnings else 0)

    write_secrets(args.vault, args.env, args.password, result.cleaned)
    print(
        f"sanitized {len(result.cleaned)} secret(s) in '{args.env}' "
        f"({result.total_changed} change(s))."
    )


def register_sanitize_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "sanitize",
        help="sanitize secret values (trim whitespace, warn on placeholders, etc.)",
    )
    p.add_argument("vault", help="path to the vault file")
    p.add_argument("env", help="environment name")
    p.add_argument("--password", required=True, help="encryption password")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="report issues without writing changes",
    )
    p.add_argument(
        "--no-strip",
        action="store_true",
        help="do not strip leading/trailing whitespace",
    )
    p.add_argument(
        "--strip-quotes",
        action="store_true",
        help="remove surrounding quote characters from values",
    )
    p.add_argument(
        "--no-warn-placeholders",
        action="store_true",
        help="suppress placeholder-value warnings",
    )
    p.add_argument(
        "--no-warn-empty",
        action="store_true",
        help="suppress empty-value warnings",
    )
    p.set_defaults(func=cmd_sanitize)
