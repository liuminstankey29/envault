"""CLI commands for promoting secrets between environments."""
from __future__ import annotations
import argparse
from envault.promote import promote_secrets


def cmd_promote(args) -> None:
    keys = args.keys if args.keys else None
    try:
        result = promote_secrets(
            vault_path=args.vault,
            src_env=args.src_env,
            dst_env=args.dst_env,
            src_password=args.src_password,
            dst_password=args.dst_password,
            keys=keys,
            overwrite=args.overwrite,
        )
    except KeyError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

    if result.promoted:
        print(f"Promoted {len(result.promoted)} new secret(s): {', '.join(result.promoted)}")
    if result.overwritten:
        print(f"Overwrote {len(result.overwritten)} existing secret(s): {', '.join(result.overwritten)}")
    if result.skipped:
        print(f"Skipped {len(result.skipped)} existing secret(s): {', '.join(result.skipped)}")
    if result.total == 0 and not result.skipped:
        print("Nothing to promote.")


def register_promote_parser(subparsers) -> None:
    p = subparsers.add_parser("promote", help="Promote secrets from one environment to another")
    p.add_argument("vault", help="Path to vault file")
    p.add_argument("src_env", help="Source environment name")
    p.add_argument("dst_env", help="Destination environment name")
    p.add_argument("--src-password", required=True, dest="src_password", help="Password for source environment")
    p.add_argument("--dst-password", required=True, dest="dst_password", help="Password for destination environment")
    p.add_argument("--keys", nargs="+", default=[], help="Specific keys to promote (default: all)")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing keys in destination")
    p.set_defaults(func=cmd_promote)
