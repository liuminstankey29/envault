"""CLI commands for archive/restore vault environments."""

from __future__ import annotations

import argparse
import sys

from envault.archive import archive_environment, restore_environment


def cmd_archive(args: argparse.Namespace) -> None:
    output = getattr(args, "output", None) or f"{args.environment}.envault.tar.gz"
    try:
        result = archive_environment(
            vault_path=args.vault,
            environment=args.environment,
            password=args.password,
            output_path=output,
            label=getattr(args, "label", None),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Archived environment '{result.environment}' "
        f"({result.key_count} keys) -> {result.archive_path}"
    )


def cmd_restore(args: argparse.Namespace) -> None:
    try:
        result = restore_environment(
            vault_path=args.vault,
            archive_path=args.archive,
            password=args.password,
            overwrite=getattr(args, "overwrite", False),
            target_environment=getattr(args, "environment", None),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Restored {result.keys_written} keys into '{result.environment}' "
        f"(skipped {result.keys_skipped})."
    )
    if result.skipped:
        print("Skipped keys: " + ", ".join(result.skipped))


def register_archive_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # archive sub-command
    p_arc = subparsers.add_parser("archive", help="Archive an environment to a bundle file")
    p_arc.add_argument("vault", help="Path to vault file")
    p_arc.add_argument("environment", help="Environment name")
    p_arc.add_argument("password", help="Encryption password")
    p_arc.add_argument("--output", "-o", help="Output file path (default: <env>.envault.tar.gz)")
    p_arc.add_argument("--label", help="Optional human-readable label for the archive")
    p_arc.set_defaults(func=cmd_archive)

    # restore sub-command
    p_rst = subparsers.add_parser("restore", help="Restore an environment from a bundle file")
    p_rst.add_argument("vault", help="Path to vault file")
    p_rst.add_argument("archive", help="Path to archive bundle")
    p_rst.add_argument("password", help="Encryption password for the target vault")
    p_rst.add_argument("--environment", "-e", help="Override target environment name")
    p_rst.add_argument("--overwrite", action="store_true", help="Overwrite existing keys")
    p_rst.set_defaults(func=cmd_restore)
