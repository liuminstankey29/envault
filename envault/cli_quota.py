"""CLI commands for quota management."""
from __future__ import annotations

import sys

from envault.quota import (
    check_quota,
    get_quota_status,
    list_quotas,
    remove_quota,
    set_quota,
)


def cmd_quota(args) -> None:
    sub = args.quota_sub

    if sub == "set":
        try:
            set_quota(args.vault, args.environment, args.limit)
            print(f"Quota set: '{args.environment}' limited to {args.limit} secrets.")
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif sub == "remove":
        removed = remove_quota(args.vault, args.environment)
        if removed:
            print(f"Quota removed for '{args.environment}'.")
        else:
            print(f"No quota was set for '{args.environment}'.")

    elif sub == "status":
        status = get_quota_status(args.vault, args.environment, args.password)
        limit_str = str(status.limit) if status.limit is not None else "unlimited"
        avail_str = str(status.available) if status.available is not None else "unlimited"
        print(f"Environment : {status.environment}")
        print(f"Limit       : {limit_str}")
        print(f"Used        : {status.used}")
        print(f"Available   : {avail_str}")
        if status.exceeded:
            print("WARNING: quota exceeded!", file=sys.stderr)
            sys.exit(2)

    elif sub == "check":
        try:
            status = check_quota(args.vault, args.environment, args.password)
            print(
                f"OK — '{args.environment}' is within quota "
                f"({status.used}/{status.limit if status.limit else '∞'})."
            )
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(2)

    elif sub == "list":
        quotas = list_quotas(args.vault)
        if not quotas:
            print("No quotas configured.")
        else:
            for env, limit in sorted(quotas.items()):
                print(f"{env}: {limit}")


def register_quota_parser(subparsers) -> None:
    p = subparsers.add_parser("quota", help="Manage per-environment secret quotas")
    p.add_argument("--vault", required=True, help="Path to vault file")
    subs = p.add_subparsers(dest="quota_sub", required=True)

    # set
    ps = subs.add_parser("set", help="Set a quota limit for an environment")
    ps.add_argument("environment")
    ps.add_argument("limit", type=int)

    # remove
    pr = subs.add_parser("remove", help="Remove quota for an environment")
    pr.add_argument("environment")

    # status
    pst = subs.add_parser("status", help="Show quota usage for an environment")
    pst.add_argument("environment")
    pst.add_argument("--password", required=True)

    # check
    pc = subs.add_parser("check", help="Exit non-zero if quota is exceeded")
    pc.add_argument("environment")
    pc.add_argument("--password", required=True)

    # list
    subs.add_parser("list", help="List all configured quotas")

    p.set_defaults(func=cmd_quota)
