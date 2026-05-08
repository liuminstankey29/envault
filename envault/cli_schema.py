"""CLI commands for schema-based secret validation."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from envault.schema import SchemaRule, validate_secrets, format_validation_results
from envault.vault import read_secrets


def _load_schema_file(path: str) -> list[SchemaRule]:
    """Parse a JSON schema file into a list of SchemaRule objects."""
    data = json.loads(Path(path).read_text())
    rules = []
    for entry in data:
        rules.append(
            SchemaRule(
                key=entry["key"],
                required=entry.get("required", True),
                pattern=entry.get("pattern"),
                min_length=entry.get("min_length"),
                max_length=entry.get("max_length"),
                allowed_values=entry.get("allowed_values"),
            )
        )
    return rules


def cmd_schema(args: Any) -> None:
    """Validate secrets in an environment against a JSON schema file."""
    rules = _load_schema_file(args.schema)
    try:
        secrets = read_secrets(args.vault, args.env, args.password)
    except Exception as exc:  # noqa: BLE001
        print(f"Error reading vault: {exc}", file=sys.stderr)
        sys.exit(1)

    result = validate_secrets(secrets, rules)

    if args.format == "json":
        output = [
            {"key": i.key, "severity": i.severity, "message": i.message}
            for i in result.issues
        ]
        print(json.dumps(output, indent=2))
    else:
        text = format_validation_results(result)
        if text:
            print(text)

    if not result.ok:
        sys.exit(2)


def register_schema_parser(subparsers: Any) -> None:
    p = subparsers.add_parser("schema", help="Validate secrets against a schema file.")
    p.add_argument("vault", help="Path to the vault file.")
    p.add_argument("env", help="Environment name to validate.")
    p.add_argument("schema", help="Path to JSON schema file.")
    p.add_argument("--password", required=True, help="Vault password.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_schema)
