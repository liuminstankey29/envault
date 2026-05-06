"""Top-level CLI entry point for envault."""

from __future__ import annotations

import argparse
import sys

from envault.vault import write_secrets, read_secrets, list_environments
from envault.cli_export import register_export_parser
from envault.cli_audit import register_audit_parser
from envault.cli_import import register_import_parser
from envault.cli_diff import register_diff_parser
from envault.cli_copy import register_copy_parser


def cmd_set(args: argparse.Namespace) -> None:
    """Set a secret in the vault."""
    try:
        secrets = read_secrets(args.vault, args.env, args.password)
    except Exception:
        secrets = {}
    secrets[args.key] = args.value
    write_secrets(args.vault, args.env, args.password, secrets)
    print(f"Set '{args.key}' in environment '{args.env}'.")


def cmd_get(args: argparse.Namespace) -> None:
    """Get a secret from the vault."""
    try:
        secrets = read_secrets(args.vault, args.env, args.password)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    if args.key not in secrets:
        print(f"Key '{args.key}' not found in environment '{args.env}'.", file=sys.stderr)
        sys.exit(1)
    print(secrets[args.key])


def cmd_list(args: argparse.Namespace) -> None:
    """List environments or keys within an environment."""
    if args.env:
        try:
            secrets = read_secrets(args.vault, args.env, args.password)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        for key in sorted(secrets):
            print(key)
    else:
        for env in list_environments(args.vault):
            print(env)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Encrypted .env file manager with per-environment secret rotation.",
    )
    sub = parser.add_subparsers(dest="command")

    # set
    p_set = sub.add_parser("set", help="Set a secret.")
    p_set.add_argument("vault"); p_set.add_argument("env")
    p_set.add_argument("key"); p_set.add_argument("value")
    p_set.add_argument("--password", required=True)
    p_set.set_defaults(func=cmd_set)

    # get
    p_get = sub.add_parser("get", help="Get a secret.")
    p_get.add_argument("vault"); p_get.add_argument("env")
    p_get.add_argument("key")
    p_get.add_argument("--password", required=True)
    p_get.set_defaults(func=cmd_get)

    # list
    p_list = sub.add_parser("list", help="List environments or keys.")
    p_list.add_argument("vault")
    p_list.add_argument("--env", default="")
    p_list.add_argument("--password", default="")
    p_list.set_defaults(func=cmd_list)

    register_export_parser(sub)
    register_audit_parser(sub)
    register_import_parser(sub)
    register_diff_parser(sub)
    register_copy_parser(sub)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
