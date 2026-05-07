"""CLI commands for tag management."""

from __future__ import annotations

import argparse
import sys

from envault.tags import add_tag, remove_tag, list_tags, filter_by_tag


def cmd_tags(args: argparse.Namespace) -> None:
    sub = args.tags_command

    if sub == "add":
        try:
            add_tag(args.vault, args.env, args.password, args.key, args.tag)
            print(f"Tag '{args.tag}' added to '{args.key}' in '{args.env}'.")
        except KeyError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif sub == "remove":
        removed = remove_tag(args.vault, args.env, args.password, args.key, args.tag)
        if removed:
            print(f"Tag '{args.tag}' removed from '{args.key}' in '{args.env}'.")
        else:
            print(f"Tag '{args.tag}' was not present on '{args.key}'.")

    elif sub == "list":
        tags = list_tags(args.vault, args.env, args.password, args.key)
        if tags:
            for t in tags:
                print(t)
        else:
            print(f"No tags for '{args.key}' in '{args.env}'.")

    elif sub == "filter":
        secrets = filter_by_tag(args.vault, args.env, args.password, args.tag)
        if not secrets:
            print(f"No secrets tagged '{args.tag}' in '{args.env}'.")
        else:
            for key, value in secrets.items():
                if args.reveal:
                    print(f"{key}={value}")
                else:
                    print(f"{key}=***")
    else:
        print(f"Unknown tags sub-command: {sub}", file=sys.stderr)
        sys.exit(1)


def register_tags_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("tags", help="Manage secret tags")
    p.add_argument("--vault", default="vault.enc", help="Vault file path")
    p.add_argument("--env", required=True, help="Environment name")
    p.add_argument("--password", required=True, help="Vault password")

    tag_sub = p.add_subparsers(dest="tags_command")
    tag_sub.required = True

    add_p = tag_sub.add_parser("add", help="Add a tag to a secret")
    add_p.add_argument("key", help="Secret key")
    add_p.add_argument("tag", help="Tag to add")

    rm_p = tag_sub.add_parser("remove", help="Remove a tag from a secret")
    rm_p.add_argument("key", help="Secret key")
    rm_p.add_argument("tag", help="Tag to remove")

    ls_p = tag_sub.add_parser("list", help="List tags for a secret")
    ls_p.add_argument("key", help="Secret key")

    fi_p = tag_sub.add_parser("filter", help="Filter secrets by tag")
    fi_p.add_argument("tag", help="Tag to filter by")
    fi_p.add_argument("--reveal", action="store_true", help="Show actual values")

    p.set_defaults(func=cmd_tags)
