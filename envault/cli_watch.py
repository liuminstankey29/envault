"""CLI surface for `envault watch`."""

from __future__ import annotations

import argparse
import sys

from envault.watch import watch_environment


def _on_change(old: dict, new: dict) -> None:
    added = set(new) - set(old)
    removed = set(old) - set(new)
    changed = {k for k in set(old) & set(new) if old[k] != new[k]}

    if added:
        for k in sorted(added):
            print(f"  [+] {k}")
    if removed:
        for k in sorted(removed):
            print(f"  [-] {k}")
    if changed:
        for k in sorted(changed):
            print(f"  [~] {k}")


def cmd_watch(args: argparse.Namespace) -> None:
    """Entry point for the `watch` sub-command."""
    vault_path: str = args.vault
    environment: str = args.environment
    password: str = args.password
    interval: float = args.interval
    shell_cmd: str | None = args.exec

    print(
        f"Watching '{environment}' in {vault_path} "
        f"(poll every {interval}s) — press Ctrl-C to stop."
    )

    try:
        watch_environment(
            vault_path,
            environment,
            password,
            interval=interval,
            on_change=_on_change,
            shell_command=shell_cmd,
        )
    except KeyboardInterrupt:
        print("\nWatch stopped.")
        sys.exit(0)


def register_watch_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("watch", help="Watch an environment for secret changes")
    p.add_argument("vault", help="Path to the vault file")
    p.add_argument("environment", help="Environment name to watch")
    p.add_argument("--password", required=True, help="Decryption password")
    p.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 2.0)",
    )
    p.add_argument(
        "--exec",
        metavar="CMD",
        default=None,
        help="Shell command to run on each detected change",
    )
    p.set_defaults(func=cmd_watch)
