"""CLI surface for the cascade feature."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envault.cascade import cascade_environments


def cmd_cascade(args: argparse.Namespace) -> None:
    """Resolve secrets by cascading through environments in priority order."""
    if len(args.envs) != len(args.passwords):
        print(
            "error: --envs and --passwords must have the same number of entries",
            file=sys.stderr,
        )
        sys.exit(1)

    pairs = list(zip(args.envs, args.passwords))
    keys: List[str] | None = args.keys if args.keys else None

    result = cascade_environments(args.vault, pairs, keys=keys)

    if result.skipped:
        print(
            f"warning: skipped environments (bad password?): {', '.join(result.skipped)}",
            file=sys.stderr,
        )

    if args.format == "json":
        payload = {
            "resolved": result.resolved,
            "sources": result.sources,
            "total": result.total,
        }
        print(json.dumps(payload, indent=2))
    elif args.format == "dotenv":
        for k, v in result.resolved.items():
            print(f'{k}="{v}"')
    else:  # table (default)
        if not result.resolved:
            print("(no secrets resolved)")
            return
        col = max(len(k) for k in result.resolved)
        print(f"{'KEY':<{col}}  {'VALUE':<30}  SOURCE")
        print("-" * (col + 40))
        for k, v in result.resolved.items():
            masked = v if args.show_values else "***"
            print(f"{k:<{col}}  {masked:<30}  {result.sources[k]}")


def register_cascade_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "cascade",
        help="Resolve secrets by merging environments in priority order",
    )
    p.add_argument("vault", help="Path to vault file")
    p.add_argument(
        "--envs", nargs="+", required=True, metavar="ENV",
        help="Environments in descending priority order",
    )
    p.add_argument(
        "--passwords", nargs="+", required=True, metavar="PASS",
        help="Passwords corresponding to each environment",
    )
    p.add_argument(
        "--keys", nargs="+", metavar="KEY",
        help="Restrict output to these keys",
    )
    p.add_argument(
        "--format", choices=["table", "dotenv", "json"], default="table",
    )
    p.add_argument(
        "--show-values", action="store_true",
        help="Print actual secret values (default: masked)",
    )
    p.set_defaults(func=cmd_cascade)
