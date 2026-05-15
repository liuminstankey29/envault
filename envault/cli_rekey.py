"""CLI sub-commands for re-keying vault environments."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.rekey import rekey_environment, rekey_all_environments


def cmd_rekey(args: argparse.Namespace) -> None:
    vault_path = Path(args.vault)

    if not vault_path.exists():
        print(f"error: vault not found: {vault_path}", file=sys.stderr)
        sys.exit(1)

    if args.environment:
        try:
            result = rekey_environment(
                vault_path,
                args.environment,
                args.old_password,
                args.new_password,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

        print(
            f"Re-keyed environment '{result.environment}': "
            f"{result.secrets_rekeyed} secret(s) re-encrypted."
        )
    else:
        results = rekey_all_environments(
            vault_path,
            args.old_password,
            args.new_password,
            skip_errors=args.skip_errors,
        )
        total_rekeyed = sum(r.secrets_rekeyed for r in results)
        skipped = [r for r in results if r.skipped]

        print(f"Re-keyed {len(results) - len(skipped)} environment(s), "
              f"{total_rekeyed} secret(s) total.")
        if skipped:
            print(f"Skipped {len(skipped)} environment(s):")
            for r in skipped:
                print(f"  {r.environment}: {r.skip_reason}")


def register_rekey_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "rekey",
        help="Re-encrypt secrets under a new master password.",
    )
    p.add_argument("--vault", required=True, help="Path to the vault file.")
    p.add_argument("--old-password", required=True, dest="old_password")
    p.add_argument("--new-password", required=True, dest="new_password")
    p.add_argument(
        "--environment",
        default=None,
        help="Re-key a single environment (default: all).",
    )
    p.add_argument(
        "--skip-errors",
        action="store_true",
        dest="skip_errors",
        help="Skip environments that cannot be decrypted instead of aborting.",
    )
    p.set_defaults(func=cmd_rekey)
