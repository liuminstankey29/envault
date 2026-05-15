"""cli_broadcast.py – CLI subcommands for webhook broadcast management."""
from __future__ import annotations

import sys
from typing import List

from envault.broadcast import add_hook, remove_hook, list_hooks, broadcast_event


def cmd_broadcast(args) -> None:  # noqa: ANN001
    sub = args.broadcast_cmd

    if sub == "add":
        added = add_hook(args.vault, args.url, events=args.events or None)
        action = "Added" if added else "Updated"
        print(f"{action} hook: {args.url}")
        if args.events:
            print(f"  Events: {', '.join(args.events)}")
        else:
            print("  Events: * (all)")

    elif sub == "remove":
        removed = remove_hook(args.vault, args.url)
        if removed:
            print(f"Removed hook: {args.url}")
        else:
            print(f"Hook not found: {args.url}", file=sys.stderr)
            sys.exit(1)

    elif sub == "list":
        hooks = list_hooks(args.vault)
        if not hooks:
            print("No webhooks registered.")
            return
        print(f"{'URL':<50}  EVENTS")
        print("-" * 70)
        for h in hooks:
            events_str = ", ".join(h.get("events", ["*"]))
            print(f"{h['url']:<50}  {events_str}")

    elif sub == "send":
        payload = {"environment": args.environment, "note": args.note or ""}
        results = broadcast_event(args.vault, args.event, payload)
        if not results:
            print("No matching hooks for that event.")
            return
        ok = sum(1 for r in results if r.success)
        print(f"Sent to {ok}/{len(results)} hooks.")
        for r in results:
            status = f"HTTP {r.status_code}" if r.status_code else "error"
            mark = "✓" if r.success else "✗"
            print(f"  {mark} {r.url}  [{status}]")
        if ok < len(results):
            sys.exit(1)

    else:
        print(f"Unknown subcommand: {sub}", file=sys.stderr)
        sys.exit(1)


def register_broadcast_parser(subparsers) -> None:  # noqa: ANN001
    p = subparsers.add_parser("broadcast", help="Manage webhook notifications")
    p.add_argument("--vault", required=True, help="Path to vault file")
    bsub = p.add_subparsers(dest="broadcast_cmd", required=True)

    # add
    pa = bsub.add_parser("add", help="Register a webhook URL")
    pa.add_argument("url", help="Webhook endpoint URL")
    pa.add_argument("--events", nargs="+", metavar="EVENT", help="Events to subscribe to (default: all)")

    # remove
    pr = bsub.add_parser("remove", help="Remove a webhook URL")
    pr.add_argument("url", help="Webhook endpoint URL")

    # list
    bsub.add_parser("list", help="List registered webhooks")

    # send
    ps = bsub.add_parser("send", help="Manually fire a broadcast event")
    ps.add_argument("event", help="Event name, e.g. secret.changed")
    ps.add_argument("--environment", default="", help="Environment name to include in payload")
    ps.add_argument("--note", default="", help="Optional note to include in payload")

    p.set_defaults(func=cmd_broadcast)
