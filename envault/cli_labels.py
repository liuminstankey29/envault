"""CLI commands for label management."""
from __future__ import annotations

import sys
from typing import Any

from envault.labels import add_label, remove_label, list_labels, filter_by_label


def cmd_labels(args: Any) -> None:
    sub = args.labels_sub

    if sub == "add":
        result = add_label(args.vault, args.environment, args.key, args.label)
        if result.added:
            print(f"Label '{args.label}' added to {args.environment}/{args.key}")
        else:
            print(f"Label '{args.label}' already present on {args.environment}/{args.key}")

    elif sub == "remove":
        result = remove_label(args.vault, args.environment, args.key, args.label)
        if result.added:  # added=True means the removal actually happened
            print(f"Label '{args.label}' removed from {args.environment}/{args.key}")
        else:
            print(f"Label '{args.label}' was not present on {args.environment}/{args.key}")

    elif sub == "list":
        mapping = list_labels(args.vault, args.environment, getattr(args, "key", None))
        if not mapping:
            print("(no labels)")
        else:
            for k, labels in sorted(mapping.items()):
                print(f"  {k}: {', '.join(sorted(labels))}")

    elif sub == "filter":
        keys = filter_by_label(args.vault, args.environment, args.label)
        if not keys:
            print(f"No keys carry label '{args.label}' in {args.environment}")
        else:
            for k in sorted(keys):
                print(k)

    else:
        print(f"Unknown labels subcommand: {sub}", file=sys.stderr)
        sys.exit(1)


def register_labels_parser(subparsers: Any) -> None:
    p = subparsers.add_parser("labels", help="Manage labels on secrets")
    p.add_argument("--vault", required=True)
    p.add_argument("--environment", "-e", required=True)
    sub = p.add_subparsers(dest="labels_sub", required=True)

    # add
    p_add = sub.add_parser("add", help="Add a label to a key")
    p_add.add_argument("key")
    p_add.add_argument("label")

    # remove
    p_rm = sub.add_parser("remove", help="Remove a label from a key")
    p_rm.add_argument("key")
    p_rm.add_argument("label")

    # list
    p_ls = sub.add_parser("list", help="List labels for an environment")
    p_ls.add_argument("key", nargs="?", default=None)

    # filter
    p_f = sub.add_parser("filter", help="Find keys carrying a specific label")
    p_f.add_argument("label")

    p.set_defaults(func=cmd_labels)
