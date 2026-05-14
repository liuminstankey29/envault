"""CLI commands for baseline capture and drift detection."""

from __future__ import annotations

import argparse
import sys

from envault.baseline import (
    capture_baseline,
    clear_baseline,
    compare_to_baseline,
    load_baseline,
)


def cmd_baseline(args: argparse.Namespace) -> None:
    action = args.baseline_action

    if action == "capture":
        hashes = capture_baseline(args.vault, args.env, args.password)
        print(f"Baseline captured for '{args.env}': {len(hashes)} key(s).")

    elif action == "status":
        diff = compare_to_baseline(args.vault, args.env, args.password)
        if diff is None:
            print(
                f"No baseline found for '{args.env}'. Run 'baseline capture' first.",
                file=sys.stderr,
            )
            sys.exit(1)
        if diff.is_clean:
            print(f"Environment '{args.env}' matches baseline. No drift detected.")
        else:
            print(f"Drift detected in '{args.env}':")
            for k in diff.added:
                print(f"  + {k}  (added)")
            for k in diff.removed:
                print(f"  - {k}  (removed)")
            for k in diff.changed:
                print(f"  ~ {k}  (changed)")
            sys.exit(2)

    elif action == "show":
        stored = load_baseline(args.vault, args.env)
        if stored is None:
            print(
                f"No baseline found for '{args.env}'.",
                file=sys.stderr,
            )
            sys.exit(1)
        for key, digest in sorted(stored.items()):
            print(f"{key}  {digest}")

    elif action == "clear":
        removed = clear_baseline(args.vault, args.env)
        if removed:
            print(f"Baseline for '{args.env}' cleared.")
        else:
            print(f"No baseline found for '{args.env}'.")


def register_baseline_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("baseline", help="Capture and compare secret baselines")
    p.add_argument("--vault", required=True, help="Path to vault file")
    p.add_argument("--env", required=True, help="Environment name")
    p.add_argument("--password", required=True, help="Vault password")
    sub = p.add_subparsers(dest="baseline_action", required=True)

    sub.add_parser("capture", help="Capture current secrets as baseline")
    sub.add_parser("status", help="Compare current secrets to baseline")
    sub.add_parser("show", help="Print stored baseline hashes")
    sub.add_parser("clear", help="Remove stored baseline")

    p.set_defaults(func=cmd_baseline)
