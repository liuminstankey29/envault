"""Secret value sanitization: strip, redact, and normalize secret values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SanitizeResult:
    cleaned: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def total_changed(self) -> int:
        return len(self.warnings)


_PLACEHOLDER_RE = re.compile(
    r'^(CHANGE_ME|REPLACE_ME|TODO|FIXME|<[^>]+>|\$\{[^}]+\}|%[A-Z_]+%)$',
    re.IGNORECASE,
)

_WHITESPACE_ONLY_RE = re.compile(r'^\s+$')


def _strip_quotes(value: str) -> Optional[str]:
    """Remove surrounding single or double quotes if balanced."""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return None


def sanitize_secrets(
    secrets: Dict[str, str],
    *,
    strip_whitespace: bool = True,
    strip_quotes: bool = False,
    warn_placeholders: bool = True,
    warn_empty: bool = True,
) -> SanitizeResult:
    """Return a sanitized copy of *secrets* with optional warnings.

    Args:
        secrets: mapping of key -> value to sanitize.
        strip_whitespace: trim leading/trailing whitespace from values.
        strip_quotes: remove surrounding quote characters.
        warn_placeholders: add a warning for placeholder-looking values.
        warn_empty: add a warning for empty or whitespace-only values.

    Returns:
        SanitizeResult with cleaned dict and list of warning strings.
    """
    result = SanitizeResult()

    for key, value in secrets.items():
        original = value

        if strip_whitespace:
            value = value.strip()

        if strip_quotes:
            unquoted = _strip_quotes(value)
            if unquoted is not None:
                value = unquoted

        if warn_empty and (value == '' or _WHITESPACE_ONLY_RE.match(value)):
            result.warnings.append(f"{key}: value is empty or whitespace-only")

        if warn_placeholders and _PLACEHOLDER_RE.match(value):
            result.warnings.append(f"{key}: value looks like a placeholder ({value!r})")

        if value != original:
            result.warnings.append(f"{key}: value was modified during sanitization")

        result.cleaned[key] = value

    return result
