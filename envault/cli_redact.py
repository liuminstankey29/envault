"""CLI sub-commands for redact: redact text or files using vault secrets."""
from __future__ import annotations

import argparse
import sys

from envault.redact import redact_text
from envault.vault import read_secrets


def cmd_redact(args: argparse.Namespace) -> None:
    try:
        secrets = read_secrets(args.vault, args.environment, args.password)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"error reading file: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        raw = args.text
    else:
        raw = sys.stdin.read()

    ignore = args.ignore or []
    result = redact_text(
        raw,
        secrets,
        mask=args.mask,
        min_value_length=args.min_length,
        ignore_keys=ignore,
    )

    if args.output and args.file:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(result.redacted_text)
        except OSError as exc:
            print(f"error writing output: {exc}", file=sys.stderr)
            sys.exit(1)
        print(
            f"Redacted {result.matches} occurrence(s) of "
            f"{len(result.redacted_keys)} secret(s) -> {args.output}"
        )
    else:
        print(result.redacted_text, end="")
        if not args.quiet:
            print(
                f"\n# {result.matches} occurrence(s) of "
                f"{len(result.redacted_keys)} secret(s) redacted.",
                file=sys.stderr,
            )


def register_redact_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("redact", help="Redact secret values from text or files")
    p.add_argument("vault", help="Path to the vault file")
    p.add_argument("environment", help="Environment name")
    p.add_argument("password", help="Vault password")
    p.add_argument("--text", help="Inline text to redact")
    p.add_argument("--file", help="Path to file to redact")
    p.add_argument("--output", "-o", help="Write redacted output to this file")
    p.add_argument("--mask", default="[REDACTED]", help="Replacement mask string")
    p.add_argument(
        "--min-length",
        type=int,
        default=3,
        dest="min_length",
        help="Minimum secret value length to redact (default: 3)",
    )
    p.add_argument(
        "--ignore",
        nargs="+",
        metavar="KEY",
        help="Keys to exclude from redaction",
    )
    p.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress summary on stderr"
    )
    p.set_defaults(func=cmd_redact)
