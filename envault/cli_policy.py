"""CLI commands for managing vault policies."""

from __future__ import annotations

import json
import sys

from envault.policy import PolicyRule, enforce_policy, load_policy, save_policy
from envault.vault import read_secrets


def cmd_policy(args) -> None:
    sub = args.policy_cmd

    if sub == "set":
        rule = PolicyRule(
            min_length=args.min_length,
            max_length=args.max_length,
            require_uppercase=args.require_uppercase,
            require_digit=args.require_digit,
            require_special=args.require_special,
            pattern=args.pattern,
            forbidden_patterns=args.forbidden_pattern or [],
        )
        save_policy(args.vault, args.environment, rule)
        print(f"Policy saved for environment '{args.environment}'.")

    elif sub == "show":
        rule = load_policy(args.vault, args.environment)
        if rule is None:
            print(f"No policy defined for environment '{args.environment}'.")
            sys.exit(1)
        if getattr(args, "format", "text") == "json":
            print(json.dumps(rule.__dict__, indent=2))
        else:
            print(f"Policy for '{args.environment}':")
            for k, v in rule.__dict__.items():
                print(f"  {k}: {v}")

    elif sub == "check":
        rule = load_policy(args.vault, args.environment)
        if rule is None:
            print(f"No policy defined for environment '{args.environment}'. Nothing to check.")
            return
        secrets = read_secrets(args.vault, args.environment, args.password)
        violations = enforce_policy(secrets, rule)
        if not violations:
            print(f"All secrets in '{args.environment}' pass the policy. ✓")
            return
        print(f"{len(violations)} policy violation(s) in '{args.environment}':")
        for v in violations:
            print(f"  [{v.rule}] {v.key}: {v.message}")
        sys.exit(2)

    else:
        print(f"Unknown policy subcommand: {sub}", file=sys.stderr)
        sys.exit(1)


def register_policy_parser(subparsers) -> None:
    p = subparsers.add_parser("policy", help="Manage secret policies per environment")
    p.add_argument("--vault", required=True, help="Path to vault file")
    p.add_argument("--environment", "-e", required=True)
    sub = p.add_subparsers(dest="policy_cmd")

    s = sub.add_parser("set", help="Define a policy for an environment")
    s.add_argument("--min-length", type=int, default=0)
    s.add_argument("--max-length", type=int, default=None)
    s.add_argument("--require-uppercase", action="store_true")
    s.add_argument("--require-digit", action="store_true")
    s.add_argument("--require-special", action="store_true")
    s.add_argument("--pattern", default=None)
    s.add_argument("--forbidden-pattern", action="append", metavar="REGEX")

    sub.add_parser("show", help="Show the policy for an environment")

    chk = sub.add_parser("check", help="Check secrets against the policy")
    chk.add_argument("--password", required=True)

    p.set_defaults(func=cmd_policy)
