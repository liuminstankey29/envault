"""CLI sub-commands for vault linting."""
from __future__ import annotations

import sys
from typing import Any

from envault.lint import lint_secrets, format_lint_results


def cmd_lint(args: Any) -> None:
    """Run lint checks on a vault environment and report issues."""
    try:
        issues = lint_secrets(
            args.vault,
            args.env,
            args.password,
            min_value_length=args.min_length,
        )
    except FileNotFoundError:
        print(f'Vault not found: {args.vault}', file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f'Error: {exc}', file=sys.stderr)
        sys.exit(1)

    output = format_lint_results(issues)
    print(output)

    error_count = sum(1 for i in issues if i.severity == 'error')
    if error_count:
        sys.exit(2)  # non-zero so CI pipelines can detect failures


def register_lint_parser(subparsers: Any) -> None:
    p = subparsers.add_parser('lint', help='Lint secrets in an environment')
    p.add_argument('vault', help='Path to vault file')
    p.add_argument('env', help='Environment name')
    p.add_argument('--password', required=True, help='Vault password')
    p.add_argument(
        '--min-length',
        dest='min_length',
        type=int,
        default=1,
        help='Minimum acceptable value length (default: 1)',
    )
    p.set_defaults(func=cmd_lint)
