"""Search secrets across environments by key pattern or value substring."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import List, Optional

from envault.vault import list_environments, read_secrets


@dataclass
class SearchResult:
    environment: str
    key: str
    value: Optional[str]  # None when show_values=False


def search_secrets(
    vault_file: str,
    password: str,
    key_pattern: Optional[str] = None,
    value_substring: Optional[str] = None,
    environments: Optional[List[str]] = None,
    show_values: bool = False,
) -> List[SearchResult]:
    """Search for secrets matching key_pattern and/or value_substring.

    Args:
        vault_file: Path to the vault file.
        password: Master password for decryption.
        key_pattern: Glob-style pattern matched against secret keys (e.g. "DB_*").
        value_substring: Case-insensitive substring matched against secret values.
        environments: Limit search to these environments; None means all.
        show_values: If True, include plaintext values in results.

    Returns:
        List of SearchResult objects ordered by (environment, key).
    """
    if key_pattern is None and value_substring is None:
        raise ValueError("At least one of key_pattern or value_substring must be provided.")

    envs = environments if environments is not None else list_environments(vault_file)
    results: List[SearchResult] = []

    for env in sorted(envs):
        try:
            secrets = read_secrets(vault_file, env, password)
        except Exception:
            continue

        for key in sorted(secrets):
            value = secrets[key]

            if key_pattern is not None and not fnmatch.fnmatch(key, key_pattern):
                continue

            if value_substring is not None and value_substring.lower() not in value.lower():
                continue

            results.append(
                SearchResult(
                    environment=env,
                    key=key,
                    value=value if show_values else None,
                )
            )

    return results


def format_search_results(results: List[SearchResult], show_values: bool = False) -> str:
    """Render search results as a human-readable string."""
    if not results:
        return "No matches found."

    lines = []
    current_env = None
    for r in results:
        if r.environment != current_env:
            if current_env is not None:
                lines.append("")
            lines.append(f"[{r.environment}]")
            current_env = r.environment
        if show_values and r.value is not None:
            lines.append(f"  {r.key} = {r.value}")
        else:
            lines.append(f"  {r.key}")
    return "\n".join(lines)
