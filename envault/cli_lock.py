"""CLI commands for environment locking."""

from __future__ import annotations

import sys
import json
from argparse import ArgumentParser, _SubParsersAction

from envault.lock import (
    lock_environment,
    unlock_environment,
    is_locked,
    get_lock_info,
    list_locked_environments,
)


def cmd_lock(args) -> None:
    sub = args.lock_sub

    if sub == "lock":
        entry = lock_environment(args.vault, args.environment, reason=getattr(args, "reason", None))
        reason_str = f" (reason: {entry['reason']}" + ")" if entry["reason"] else ""
        print(f"Locked environment '{args.environment}'{reason_str}.")

    elif sub == "unlock":
        was_locked = unlock_environment(args.vault, args.environment)
        if was_locked:
            print(f"Unlocked environment '{args.environment}'.")
        else:
            print(f"Environment '{args.environment}' was not locked.")

    elif sub == "status":
        info = get_lock_info(args.vault, args.environment)
        if info:
            reason_str = f", reason: {info['reason']}" if info["reason"] else ""
            print(f"LOCKED{reason_str}")
        else:
            print("UNLOCKED")

    elif sub == "list":
        locks = list_locked_environments(args.vault)
        if not locks:
            print("No environments are locked.")
            return
        if getattr(args, "json", False):
            print(json.dumps(locks, indent=2))
        else:
            for env, info in sorted(locks.items()):
                reason_str = f"  reason: {info['reason']}" if info.get("reason") else ""
                print(f"  {env}{reason_str}")
    else:
        print(f"Unknown lock subcommand: {sub}", file=sys.stderr)
        sys.exit(1)


def register_lock_parser(subparsers: _SubParsersAction) -> None:
    p = subparsers.add_parser("lock", help="Lock or unlock environments")
    p.set_defaults(func=cmd_lock)
    subs = p.add_subparsers(dest="lock_sub", required=True)

    # lock
    p_lock = subs.add_parser("lock", help="Lock an environment")
    p_lock.add_argument("vault", help="Path to vault file")
    p_lock.add_argument("environment", help="Environment name")
    p_lock.add_argument("--reason", default="", help="Optional lock reason")

    # unlock
    p_unlock = subs.add_parser("unlock", help="Unlock an environment")
    p_unlock.add_argument("vault", help="Path to vault file")
    p_unlock.add_argument("environment", help="Environment name")

    # status
    p_status = subs.add_parser("status", help="Check lock status of an environment")
    p_status.add_argument("vault", help="Path to vault file")
    p_status.add_argument("environment", help="Environment name")

    # list
    p_list = subs.add_parser("list", help="List all locked environments")
    p_list.add_argument("vault", help="Path to vault file")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")
