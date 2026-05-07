"""CLI sub-commands for template rendering."""
from __future__ import annotations

import argparse
import sys

from envault.template import render_template_file


def cmd_template(args: argparse.Namespace) -> None:
    """Handle the ``envault template render`` sub-command."""
    try:
        rendered = render_template_file(
            template_path=args.template,
            vault_path=args.vault,
            environment=args.environment,
            password=args.password,
            output_path=getattr(args, "output", None),
            strict=not args.loose,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, "output", None):
        print(f"Rendered template written to {args.output}")
    else:
        print(rendered, end="")


def register_template_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the ``template`` command group to *subparsers*."""
    tp = subparsers.add_parser("template", help="Render templates with vault secrets")
    sub = tp.add_subparsers(dest="template_cmd", required=True)

    render_p = sub.add_parser("render", help="Fill placeholders in a template file")
    render_p.add_argument("template", help="Path to the template file")
    render_p.add_argument("-e", "--environment", required=True, help="Vault environment")
    render_p.add_argument("-p", "--password", required=True, help="Vault password")
    render_p.add_argument("-v", "--vault", default="vault.enc", help="Vault file path")
    render_p.add_argument("-o", "--output", default=None, help="Write rendered output here")
    render_p.add_argument(
        "--loose",
        action="store_true",
        help="Leave unknown placeholders unchanged instead of raising an error",
    )
    render_p.set_defaults(func=cmd_template)
