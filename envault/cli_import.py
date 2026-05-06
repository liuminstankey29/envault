"""CLI commands for importing secrets into a vault from external files."""

import argparse
import sys
from typing import Optional

from envault.import_env import import_secrets
from envault.audit import record_event


def cmd_import(args, out=None):
    """Handle the 'import' subcommand."""
    if out is None:
        out = sys.stdout

    try:
        written = import_secrets(
            vault_path=args.vault,
            environment=args.environment,
            password=args.password,
            import_path=args.file,
            overwrite=getattr(args, "overwrite", False),
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"Error parsing import file: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    count = len(written)
    record_event(
        log_path=getattr(args, "audit_log", None),
        event="import",
        environment=args.environment,
        detail={"keys_imported": count, "source": args.file, "overwrite": getattr(args, "overwrite", False)},
    )

    if count == 0:
        print("No new secrets imported (use --overwrite to replace existing keys).", file=out)
    else:
        print(f"Imported {count} secret(s) into environment '{args.environment}'.", file=out)
        for key in sorted(written):
            print(f"  + {key}", file=out)


def register_import_parser(subparsers):
    """Register the 'import' subcommand onto an existing subparsers object."""
    p = subparsers.add_parser(
        "import",
        help="Import secrets from a .env or JSON file into a vault environment",
    )
    p.add_argument("environment", help="Target environment name (e.g. production)")
    p.add_argument("file", help="Path to the .env or .json file to import")
    p.add_argument("-v", "--vault", default="vault.enc", help="Path to vault file")
    p.add_argument("-p", "--password", required=True, help="Vault password")
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys with values from the import file",
    )
    p.set_defaults(func=cmd_import)
    return p
