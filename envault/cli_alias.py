"""CLI commands for environment alias management."""

from __future__ import annotations

import argparse
import sys

from envault.alias import (
    set_alias,
    remove_alias,
    resolve_alias,
    list_aliases,
    get_alias_target,
)


def cmd_alias(args: argparse.Namespace) -> None:
    vault = args.vault

    if args.alias_action == "set":
        is_new = set_alias(vault, args.alias, args.environment)
        verb = "Created" if is_new else "Updated"
        print(f"{verb} alias '{args.alias}' -> '{args.environment}'")

    elif args.alias_action == "remove":
        removed = remove_alias(vault, args.alias)
        if removed:
            print(f"Removed alias '{args.alias}'")
        else:
            print(f"Alias '{args.alias}' not found.", file=sys.stderr)
            sys.exit(1)

    elif args.alias_action == "resolve":
        target = resolve_alias(vault, args.alias)
        print(target)

    elif args.alias_action == "list":
        aliases = list_aliases(vault)
        if not aliases:
            print("No aliases defined.")
        else:
            width = max(len(a) for a in aliases)
            for alias, env in sorted(aliases.items()):
                print(f"  {alias:<{width}}  ->  {env}")

    elif args.alias_action == "get":
        target = get_alias_target(vault, args.alias)
        if target is None:
            print(f"Alias '{args.alias}' not found.", file=sys.stderr)
            sys.exit(1)
        print(target)


def register_alias_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("alias", help="Manage environment aliases")
    p.add_argument("--vault", required=True, help="Path to vault file")
    sub = p.add_subparsers(dest="alias_action", required=True)

    s = sub.add_parser("set", help="Create or update an alias")
    s.add_argument("alias", help="Alias name")
    s.add_argument("environment", help="Target environment name")

    r = sub.add_parser("remove", help="Remove an alias")
    r.add_argument("alias", help="Alias name to remove")

    sub.add_parser("list", help="List all aliases")

    rs = sub.add_parser("resolve", help="Resolve an alias to its target")
    rs.add_argument("alias", help="Alias or environment name")

    g = sub.add_parser("get", help="Get the target of a specific alias")
    g.add_argument("alias", help="Alias name")

    p.set_defaults(func=cmd_alias)
