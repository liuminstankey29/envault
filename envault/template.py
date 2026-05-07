"""Template rendering: substitute vault secrets into template strings."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from envault.vault import read_secrets

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_template(template: str, secrets: dict[str, str], strict: bool = True) -> str:
    """Replace ``{{ KEY }}`` placeholders with values from *secrets*.

    Parameters
    ----------
    template:
        Raw template text.
    secrets:
        Mapping of secret keys to plaintext values.
    strict:
        When *True* (default) raise ``KeyError`` for any placeholder whose
        key is absent from *secrets*.  When *False*, leave the placeholder
        unchanged.
    """
    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key in secrets:
            return secrets[key]
        if strict:
            raise KeyError(f"Template placeholder '{{{{{key}}}}}' not found in secrets")
        return match.group(0)

    return _PLACEHOLDER.sub(_replace, template)


def render_template_file(
    template_path: str | Path,
    vault_path: str | Path,
    environment: str,
    password: str,
    output_path: Optional[str | Path] = None,
    strict: bool = True,
) -> str:
    """Read a template file, fill placeholders from the vault, and optionally
    write the result to *output_path*.  Always returns the rendered string.
    """
    template_path = Path(template_path)
    template_text = template_path.read_text(encoding="utf-8")

    secrets = read_secrets(str(vault_path), environment, password)
    rendered = render_template(template_text, secrets, strict=strict)

    if output_path is not None:
        Path(output_path).write_text(rendered, encoding="utf-8")

    return rendered
