"""Export secrets to various shell-compatible formats."""

from __future__ import annotations

from typing import Dict, Literal

ExportFormat = Literal["dotenv", "shell", "json"]


def format_dotenv(secrets: Dict[str, str]) -> str:
    """Format secrets as a .env file (KEY=VALUE)."""
    lines = []
    for key, value in sorted(secrets.items()):
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def format_shell(secrets: Dict[str, str]) -> str:
    """Format secrets as shell export statements."""
    lines = []
    for key, value in sorted(secrets.items()):
        escaped = value.replace('"', '\\"')
        lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def format_json(secrets: Dict[str, str]) -> str:
    """Format secrets as a JSON object."""
    import json
    return json.dumps(secrets, indent=2, sort_keys=True) + "\n"


FORMAT_HANDLERS = {
    "dotenv": format_dotenv,
    "shell": format_shell,
    "json": format_json,
}


def export_secrets(secrets: Dict[str, str], fmt: ExportFormat = "dotenv") -> str:
    """Export secrets dict to the requested string format."""
    if fmt not in FORMAT_HANDLERS:
        raise ValueError(
            f"Unknown format {fmt!r}. Choose from: {', '.join(FORMAT_HANDLERS)}"
        )
    return FORMAT_HANDLERS[fmt](secrets)
