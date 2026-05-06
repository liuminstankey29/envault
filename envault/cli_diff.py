"""CLI commands for diffing environments."""

from __future__ import annotations

import argparse
import getpass
import sys

from .diff import diff_environments, format_diff


def cmd_diff(args: argparse.Namespace) -> None:
    """Handle the 'diff' subcommand."""
    password_a = args.password_a or getpass.getpass(
        f"Password for environment '{args.env_a}': "
    )
    password_b = args.password_b or getpass.getpass(
        f"Password for environment '{args.env_b}': "
    )

    try:
        entries = diff_environments(
            vault_path=args.vault,
            env_a=args.env_a,
            password_a=password_a,
            env_b=args.env_b,
            password_b=password_b,
            show_unchanged=args.show_unchanged,
        )
    except KeyError as exc:
        print(f"Error: environment {exc} not found in vault.", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    mask = not args.reveal
    output = format_diff(entries, mask_values=mask)
    print(output)

    added = sum(1 for e in entries if e.status == "added")
    removed = sum(1 for e in entries if e.status == "removed")
    changed = sum(1 for e in entries if e.status == "changed")
    print(
        f"\nSummary: {added} added, {removed} removed, {changed} changed.",
        file=sys.stderr,
    )


def register_diff_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'diff' subcommand on the given subparsers action."""
    p = subparsers.add_parser(
        "diff",
        help="Diff secrets between two environments",
    )
    p.add_argument("env_a", help="First environment name")
    p.add_argument("env_b", help="Second environment name")
    p.add_argument("--vault", default="vault.json", help="Path to vault file")
    p.add_argument("--password-a", dest="password_a", default=None)
    p.add_argument("--password-b", dest="password_b", default=None)
    p.add_argument(
        "--show-unchanged",
        dest="show_unchanged",
        action="store_true",
        default=False,
        help="Also show keys that are identical in both environments",
    )
    p.add_argument(
        "--reveal",
        action="store_true",
        default=False,
        help="Show actual secret values instead of masking them",
    )
    p.set_defaults(func=cmd_diff)
