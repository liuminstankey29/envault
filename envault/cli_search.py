"""CLI sub-commands for searching secrets in the vault."""

from __future__ import annotations

import argparse
import json
import sys

from envault.search import format_search_results, search_secrets


def cmd_search(args: argparse.Namespace) -> None:
    """Handle the `envault search` command."""
    try:
        results = search_secrets(
            vault_file=args.vault,
            password=args.password,
            key_pattern=args.key_pattern,
            value_substring=args.value_contains,
            environments=args.env or None,
            show_values=args.show_values,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: vault file '{args.vault}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        output = [
            {
                "environment": r.environment,
                "key": r.key,
                **(({"value": r.value}) if args.show_values else {}),
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        print(format_search_results(results, show_values=args.show_values))


def register_search_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the `search` sub-command onto an existing subparsers group."""
    p = subparsers.add_parser(
        "search",
        help="Search secrets across environments by key pattern or value substring.",
    )
    p.add_argument("--vault", required=True, help="Path to the vault file.")
    p.add_argument("--password", required=True, help="Master password.")
    p.add_argument(
        "--key-pattern",
        dest="key_pattern",
        default=None,
        metavar="PATTERN",
        help="Glob pattern for key names (e.g. 'DB_*').",
    )
    p.add_argument(
        "--value-contains",
        dest="value_contains",
        default=None,
        metavar="TEXT",
        help="Case-insensitive substring to match against values.",
    )
    p.add_argument(
        "--env",
        nargs="+",
        metavar="ENV",
        help="Limit search to specific environments.",
    )
    p.add_argument(
        "--show-values",
        action="store_true",
        help="Include plaintext values in output (sensitive).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_search)
