"""CLI sub-commands: compare."""
from __future__ import annotations

import argparse
import sys

from envault.compare import compare_environments, format_compare_result


def cmd_compare(args: argparse.Namespace) -> None:
    try:
        result = compare_environments(
            vault_path=args.vault,
            env_a=args.env_a,
            password_a=args.password_a,
            env_b=args.env_b,
            password_b=getattr(args, "password_b", None) or args.password_a,
            vault_path_b=getattr(args, "vault_b", None),
        )
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    output = format_compare_result(
        result,
        env_a=args.env_a,
        env_b=args.env_b,
        show_counts=True,
    )
    print(output)

    if not result.is_identical:
        sys.exit(1)


def register_compare_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "compare",
        help="Compare secrets between two environments.",
    )
    p.add_argument("vault", help="Path to the primary vault file.")
    p.add_argument("env_a", metavar="ENV_A", help="First environment name.")
    p.add_argument("env_b", metavar="ENV_B", help="Second environment name.")
    p.add_argument(
        "--password-a",
        required=True,
        metavar="PASS",
        help="Password for ENV_A (also used for ENV_B unless --password-b given).",
    )
    p.add_argument(
        "--password-b",
        default=None,
        metavar="PASS",
        help="Password for ENV_B if different from ENV_A.",
    )
    p.add_argument(
        "--vault-b",
        default=None,
        metavar="PATH",
        help="Path to a second vault file for ENV_B (optional).",
    )
    p.set_defaults(func=cmd_compare)
