"""Promote secrets from one environment to another (e.g. staging -> production)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.vault import read_secrets, write_secrets


@dataclass
class PromoteResult:
    source: str
    destination: str
    promoted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.promoted) + len(self.overwritten)


def promote_secrets(
    vault_path: str,
    src_env: str,
    src_password: str,
    dst_env: str,
    dst_password: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> PromoteResult:
    """Copy secrets from *src_env* into *dst_env*.

    Parameters
    ----------
    vault_path:   Path to the vault file.
    src_env:      Source environment name.
    src_password: Password for the source environment.
    dst_env:      Destination environment name.
    dst_password: Password for the destination environment.
    keys:         Optional list of specific keys to promote.  Promotes all
                  source keys when *None*.
    overwrite:    When *True*, existing destination keys are replaced.
                  When *False* (default), they are left untouched and
                  recorded in ``result.skipped``.
    """
    src_secrets = read_secrets(vault_path, src_env, src_password)
    dst_secrets = read_secrets(vault_path, dst_env, dst_password) if _env_exists(vault_path, dst_env) else {}

    candidates = {k: v for k, v in src_secrets.items() if keys is None or k in keys}

    if keys:
        missing = set(keys) - set(src_secrets)
        if missing:
            raise KeyError(f"Keys not found in '{src_env}': {sorted(missing)}")

    result = PromoteResult(source=src_env, destination=dst_env)

    for key, value in candidates.items():
        if key in dst_secrets:
            if overwrite:
                dst_secrets[key] = value
                result.overwritten.append(key)
            else:
                result.skipped.append(key)
        else:
            dst_secrets[key] = value
            result.promoted.append(key)

    write_secrets(vault_path, dst_env, dst_password, dst_secrets)
    return result


def _env_exists(vault_path: str, env: str) -> bool:
    from envault.vault import list_environments
    try:
        return env in list_environments(vault_path)
    except FileNotFoundError:
        return False
