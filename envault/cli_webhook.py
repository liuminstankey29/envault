"""CLI commands for webhook management."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, _SubParsersAction
from typing import Any

from envault.webhook import deliver_webhook, list_webhooks, register_webhook, remove_webhook


def cmd_webhook(args: Any) -> None:
    sub = args.webhook_cmd

    if sub == "add":
        events = args.events.split(",") if args.events else None
        is_new = register_webhook(args.vault, args.name, args.url, events)
        status = "Registered" if is_new else "Updated"
        print(f"{status} webhook '{args.name}' -> {args.url}")
        if events:
            print(f"  Events: {', '.join(events)}")
        else:
            print("  Events: * (all)")

    elif sub == "remove":
        removed = remove_webhook(args.vault, args.name)
        if removed:
            print(f"Removed webhook '{args.name}'.")
        else:
            print(f"Webhook '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    elif sub == "list":
        hooks = list_webhooks(args.vault)
        if not hooks:
            print("No webhooks registered.")
            return
        if getattr(args, "format", "text") == "json":
            print(json.dumps(hooks, indent=2))
        else:
            for name, cfg in hooks.items():
                events = ", ".join(cfg.get("events", ["*"]))
                print(f"  {name}: {cfg['url']}  [{events}]")

    elif sub == "deliver":
        payload = {}
        if args.payload:
            try:
                payload = json.loads(args.payload)
            except json.JSONDecodeError:
                print("--payload must be valid JSON.", file=sys.stderr)
                sys.exit(1)
        results = deliver_webhook(args.vault, args.event, payload)
        if not results:
            print("No matching webhooks for this event.")
            return
        for r in results:
            mark = "OK" if r.success else "FAIL"
            detail = f" ({r.error}" if r.error else ""
            print(f"  [{mark}] {r.url}  HTTP {r.status_code}{detail}")
        if any(not r.success for r in results):
            sys.exit(1)


def register_webhook_parser(subparsers: _SubParsersAction) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser("webhook", help="Manage webhooks")
    p.add_argument("vault", help="Vault file path")
    ws = p.add_subparsers(dest="webhook_cmd", required=True)

    add_p = ws.add_parser("add", help="Register a webhook")
    add_p.add_argument("name", help="Unique webhook name")
    add_p.add_argument("url", help="Endpoint URL")
    add_p.add_argument("--events", help="Comma-separated event names (default: all)", default=None)

    rm_p = ws.add_parser("remove", help="Remove a webhook")
    rm_p.add_argument("name", help="Webhook name")

    ls_p = ws.add_parser("list", help="List webhooks")
    ls_p.add_argument("--format", choices=["text", "json"], default="text")

    dl_p = ws.add_parser("deliver", help="Manually deliver an event")
    dl_p.add_argument("event", help="Event name")
    dl_p.add_argument("--payload", help="JSON payload string", default=None)

    p.set_defaults(func=cmd_webhook)
