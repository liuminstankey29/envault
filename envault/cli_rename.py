"""CLI sub-commands for renaming secrets."""

import sys
from envault.rename import rename_secret, rename_secret_across_environments


def cmd_rename(args) -> None:
    """
    Handle the `envault rename` sub-command.

    If --all-envs is given, the rename is applied to every environment.
    Otherwise, --env is required.
    """
    vault = args.vault
    old_key = args.old_key
    new_key = args.new_key
    password = args.password
    overwrite = getattr(args, "overwrite", False)

    if getattr(args, "all_envs", False):
        results = rename_secret_across_environments(
            vault, old_key, new_key, password, overwrite=overwrite
        )
        if not results:
            print(f"Key '{old_key}' not found in any environment.", file=sys.stderr)
            sys.exit(1)
        for r in results:
            _print_result(r, include_env=True)
    else:
        if not args.env:
            print("--env is required unless --all-envs is specified.", file=sys.stderr)
            sys.exit(1)
        try:
            result = rename_secret(vault, args.env, old_key, new_key, password, overwrite=overwrite)
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        _print_result(result, include_env=False)


def _print_result(result: dict, include_env: bool) -> None:
    prefix = f"[{result['env']}] " if include_env else ""
    if result["skipped"]:
        print(f"{prefix}SKIPPED: '{result['old_key']}' -> '{result['new_key']}' (key already exists; use --overwrite)")
    else:
        print(f"{prefix}RENAMED: '{result['old_key']}' -> '{result['new_key']}'")


def register_rename_parser(subparsers) -> None:
    p = subparsers.add_parser("rename", help="Rename a secret key within an environment.")
    p.add_argument("old_key", help="Existing key name.")
    p.add_argument("new_key", help="New key name.")
    p.add_argument("--env", default=None, help="Target environment.")
    p.add_argument("--all-envs", action="store_true", dest="all_envs",
                   help="Apply rename across all environments.")
    p.add_argument("--overwrite", action="store_true",
                   help="Overwrite new_key if it already exists.")
    p.set_defaults(func=cmd_rename)
