"""Redact secrets from arbitrary text strings."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RedactResult:
    redacted_text: str
    matches: int
    redacted_keys: List[str] = field(default_factory=list)


def _default_mask(key: str) -> str:
    return "[REDACTED]"


def redact_text(
    text: str,
    secrets: Dict[str, str],
    mask: str = "[REDACTED]",
    min_value_length: int = 3,
    ignore_keys: Optional[List[str]] = None,
) -> RedactResult:
    """Replace all occurrences of secret values in *text* with *mask*.

    Args:
        text: The input string to sanitise.
        secrets: Mapping of key -> plaintext value.
        mask: Replacement string (default ``[REDACTED]``).
        min_value_length: Values shorter than this are skipped to avoid
            over-aggressive redaction of common substrings.
        ignore_keys: Keys whose values should not be redacted.

    Returns:
        A :class:`RedactResult` with the sanitised text and match metadata.
    """
    ignore_keys = ignore_keys or []
    result = text
    matches = 0
    redacted_keys: List[str] = []

    # Sort by value length descending so longer secrets are replaced first,
    # preventing partial matches from hiding full matches.
    sorted_items = sorted(
        (
            (k, v)
            for k, v in secrets.items()
            if k not in ignore_keys and len(v) >= min_value_length
        ),
        key=lambda kv: len(kv[1]),
        reverse=True,
    )

    for key, value in sorted_items:
        if value in result:
            count = result.count(value)
            result = result.replace(value, mask)
            matches += count
            redacted_keys.append(key)

    return RedactResult(redacted_text=result, matches=matches, redacted_keys=redacted_keys)
