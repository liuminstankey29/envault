"""CLI command for generating vault health reports."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from envault.report import build_environment_report, build_vault_report


def cmd_report(args) -> None:
    vault_path = Path(args.vault)

    if args.environment:
        passwords = {args.environment: args.password}
        rep = build_environment_report(vault_path, args.environment, args.password)
        envs = [rep]
    else:
        # For multi-env, accept a single shared password or per-env via --password
        from envault.vault import list_environments
        envs_list = list_environments(vault_path)
        passwords = {e: args.password for e in envs_list}
        vault_rep = build_vault_report(vault_path, passwords)
        envs = vault_rep.environments

    if args.format == "json":
        output = [
            {
                "environment": e.environment,
                "secret_count": e.secret_count,
                "locked": e.locked,
                "lint_errors": e.lint_errors,
                "lint_warnings": e.lint_warnings,
                "expired_keys": e.expired_keys,
                "quota_pct": e.quota_pct,
            }
            for e in envs
        ]
        print(json.dumps(output, indent=2))
        return

    # Text table output
    header = f"{'ENV':<20} {'SECRETS':>7} {'LOCKED':>6} {'ERRORS':>6} {'WARNS':>5} {'EXPIRED':>7} {'QUOTA%':>7}"
    print(header)
    print("-" * len(header))
    for e in envs:
        locked_str = "yes" if e.locked else "no"
        quota_str = f"{e.quota_pct:.1f}" if e.quota_pct is not None else "N/A"
        expired_str = str(len(e.expired_keys))
        print(
            f"{e.environment:<20} {e.secret_count:>7} {locked_str:>6} "
            f"{e.lint_errors:>6} {e.lint_warnings:>5} {expired_str:>7} {quota_str:>7}"
        )

    total_errors = sum(e.lint_errors for e in envs)
    if total_errors > 0:
        sys.exit(2)


def register_report_parser(subparsers) -> None:
    p = subparsers.add_parser("report", help="Generate a vault health report")
    p.add_argument("vault", help="Path to the vault file")
    p.add_argument("--password", required=True, help="Decryption password")
    p.add_argument("--environment", "--env", help="Limit report to one environment")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_report)
