"""CLI sub-commands for export and rotate operations."""

from __future__ import annotations

import sys

from envault.export import export_secrets
from envault.rotate import rotate_environment, rotate_all_environments
from envault.vault import read_secrets, list_environments


def cmd_export(args) -> None:
    """Handle the 'export' sub-command."""
    secrets = read_secrets(args.vault, args.environment, args.password)
    if not secrets:
        print(
            f"No secrets found for environment '{args.environment}'.",
            file=sys.stderr,
        )
        sys.exit(1)
    output = export_secrets(secrets, fmt=args.format)
    print(output, end="")


def cmd_rotate(args) -> None:
    """Handle the 'rotate' sub-command."""
    if args.all_environments:
        envs = list_environments(args.vault)
        if not envs:
            print("No environments found in vault.", file=sys.stderr)
            sys.exit(1)
        results = rotate_all_environments(
            args.vault, args.old_password, args.new_password, envs
        )
        for env, count in results.items():
            print(f"  {env}: {count} secret(s) rotated")
    else:
        count = rotate_environment(
            args.vault, args.environment, args.old_password, args.new_password
        )
        print(f"Rotated {count} secret(s) in '{args.environment}'.")


def register_export_parser(subparsers) -> None:
    """Attach export + rotate parsers to an existing subparsers group."""
    # --- export ---
    p_export = subparsers.add_parser(
        "export", help="Print secrets in shell-friendly format"
    )
    p_export.add_argument("environment", help="Environment name")
    p_export.add_argument(
        "--format",
        choices=["dotenv", "shell", "json"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    p_export.set_defaults(func=cmd_export)

    # --- rotate ---
    p_rotate = subparsers.add_parser(
        "rotate", help="Re-encrypt secrets with a new password"
    )
    p_rotate.add_argument(
        "environment",
        nargs="?",
        default=None,
        help="Environment to rotate (omit with --all)",
    )
    p_rotate.add_argument("--old-password", required=True, dest="old_password")
    p_rotate.add_argument("--new-password", required=True, dest="new_password")
    p_rotate.add_argument(
        "--all",
        dest="all_environments",
        action="store_true",
        help="Rotate every environment in the vault",
    )
    p_rotate.set_defaults(func=cmd_rotate)
