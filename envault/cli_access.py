"""CLI commands for access control management."""
from __future__ import annotations

import sys
from typing import List

from envault.access import (
    AccessRule,
    can_read,
    can_write,
    get_access_rule,
    list_access_rules,
    remove_access_rule,
    set_access_rule,
)


def cmd_access(args) -> None:
    sub = args.access_cmd

    if sub == "set":
        readable = args.readable or []
        writable = args.writable or []
        rule = AccessRule(
            role=args.role,
            environment=args.environment,
            readable_keys=readable,
            writable_keys=writable,
        )
        set_access_rule(args.vault, rule)
        print(
            f"Access rule set: role={args.role!r} env={args.environment!r} "
            f"readable={readable or '(all)'} writable={writable or '(none)'}"
        )

    elif sub == "remove":
        removed = remove_access_rule(args.vault, args.environment, args.role)
        if removed:
            print(f"Removed access rule for role={args.role!r} in env={args.environment!r}.")
        else:
            print(f"No rule found for role={args.role!r} in env={args.environment!r}.")
            sys.exit(1)

    elif sub == "show":
        rule = get_access_rule(args.vault, args.environment, args.role)
        if rule is None:
            print(f"No access rule for role={args.role!r} in env={args.environment!r}.")
            sys.exit(1)
        print(f"Role      : {rule.role}")
        print(f"Env       : {rule.environment}")
        print(f"Readable  : {', '.join(rule.readable_keys) or '(all)'}")
        print(f"Writable  : {', '.join(rule.writable_keys) or '(none)'}")

    elif sub == "list":
        rules = list_access_rules(args.vault, environment=getattr(args, "environment", None))
        if not rules:
            print("No access rules defined.")
            return
        print(f"{'ROLE':<20} {'ENV':<20} {'READABLE':<30} {'WRITABLE':<30}")
        print("-" * 100)
        for r in rules:
            print(
                f"{r.role:<20} {r.environment:<20} "
                f"{', '.join(r.readable_keys) or '(all)':<30} "
                f"{', '.join(r.writable_keys) or '(none)':<30}"
            )

    elif sub == "check":
        action = args.action
        key = args.key
        ok = can_read(args.vault, args.environment, args.role, key) if action == "read" \
            else can_write(args.vault, args.environment, args.role, key)
        status = "ALLOWED" if ok else "DENIED"
        print(f"{action.upper()} {key!r} by role={args.role!r} in env={args.environment!r}: {status}")
        if not ok:
            sys.exit(1)


def register_access_parser(subparsers) -> None:
    p = subparsers.add_parser("access", help="Manage per-environment access control rules")
    sp = p.add_subparsers(dest="access_cmd", required=True)

    def _common(sub_p):
        sub_p.add_argument("--vault", required=True)
        sub_p.add_argument("--environment", required=True)
        sub_p.add_argument("--role", required=True)

    s = sp.add_parser("set", help="Set an access rule")
    _common(s)
    s.add_argument("--readable", nargs="*", metavar="KEY")
    s.add_argument("--writable", nargs="*", metavar="KEY")

    r = sp.add_parser("remove", help="Remove an access rule")
    _common(r)

    sh = sp.add_parser("show", help="Show a specific access rule")
    _common(sh)

    ls = sp.add_parser("list", help="List access rules")
    ls.add_argument("--vault", required=True)
    ls.add_argument("--environment", default=None)

    ck = sp.add_parser("check", help="Check if a role can read/write a key")
    _common(ck)
    ck.add_argument("--action", choices=["read", "write"], required=True)
    ck.add_argument("--key", required=True)

    p.set_defaults(func=cmd_access)
