"""Cascade: resolve secrets by merging multiple environments in priority order."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from envault.vault import read_secrets


@dataclass
class CascadeResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    # maps key -> (environment it was sourced from)
    sources: Dict[str, str] = field(default_factory=dict)
    # environments that were skipped because they couldn't be decrypted
    skipped: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.resolved)


def cascade_environments(
    vault_path: str,
    environments: List[Tuple[str, str]],  # [(env_name, password), ...]
    keys: Optional[List[str]] = None,
) -> CascadeResult:
    """Merge secrets from multiple environments in priority order.

    Earlier entries in *environments* take precedence over later ones.
    If *keys* is given, only those keys are included in the result.
    """
    result = CascadeResult()

    for env_name, password in environments:
        try:
            secrets = read_secrets(vault_path, env_name, password)
        except Exception:
            result.skipped.append(env_name)
            continue

        for k, v in secrets.items():
            if keys is not None and k not in keys:
                continue
            if k not in result.resolved:
                result.resolved[k] = v
                result.sources[k] = env_name

    return result
