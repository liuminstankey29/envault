"""CLI sub-commands for managing notification hooks."""
from __future__ import annotations

import argparse
import json
import sys

from envault.notify import add_notify_hook, remove_notify_hook, list_notify_hooks, fire_event


def cmd_notify(args: argparse.Namespace) -> None:
    sub = args.notify_sub

    if sub == "add":
        added = add_notify_hook(args.vault, args.event, args.url)
        if added:
            print(f"Added hook for '{args.event}': {args.url}")
        else:
            print(f"Hook already registered for '{args.event}': {args.url}")

    elif sub == "remove":
        removed = remove_notify_hook(args.vault, args.event, args.url)
        if removed:
            print(f"Removed hook for '{args.event}': {args.url}")
        else:
            print(f"Hook not found for '{args.event}': {args.url}", file=sys.stderr)
            sys.exit(1)

    elif sub == "list":
        hooks = list_notify_hooks(args.vault)
        if args.format == "json":
            print(json.dumps(hooks, indent=2))
        else:
            if not hooks:
                print("No notification hooks registered.")
                return
            for event, urls in sorted(hooks.items()):
                for url in urls:
                    print(f"{event:20s}  {url}")

    elif sub == "fire":
        payload = {}
        if args.payload:
            try:
                payload = json.loads(args.payload)
            except json.JSONDecodeError as exc:
                print(f"Invalid JSON payload: {exc}", file=sys.stderr)
                sys.exit(1)
        results = fire_event(args.vault, args.event, payload)
        if not results:
            print(f"No hooks registered for event '{args.event}'.")
            return
        for r in results:
            status = r.status_code if r.status_code is not None else "err"
            mark = "OK" if r.success else "FAIL"
            print(f"[{mark}] {r.url} ({status})")
        if any(not r.success for r in results):
            sys.exit(1)


def register_notify_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("notify", help="Manage notification webhooks")
    p.add_argument("--vault", required=True, help="Path to vault file")
    subs = p.add_subparsers(dest="notify_sub", required=True)

    add_p = subs.add_parser("add", help="Register a webhook URL for an event")
    add_p.add_argument("event", help="Event name, e.g. 'rotate', 'expire', 'set'")
    add_p.add_argument("url", help="Webhook URL")

    rm_p = subs.add_parser("remove", help="Unregister a webhook URL")
    rm_p.add_argument("event")
    rm_p.add_argument("url")

    ls_p = subs.add_parser("list", help="List registered webhooks")
    ls_p.add_argument("--format", choices=["text", "json"], default="text")

    fire_p = subs.add_parser("fire", help="Manually fire an event")
    fire_p.add_argument("event")
    fire_p.add_argument("--payload", default=None, help="JSON string to include in POST body")

    p.set_defaults(func=cmd_notify)
