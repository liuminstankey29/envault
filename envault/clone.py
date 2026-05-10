"""Clone an entire environment to a new environment within the same vault."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from envault.vault import read_secrets, write_secrets


@dataclass
class CloneResult:
    source: str
    destination: str
    copied: int
    skipped: int
    overwritten: int

    @property
    def total(self) -> int:
        return self.copied + self.skipped + self.overwritten


def clone_environment(
    vault_path: str,
    src_env: str,
    src_password: str,
    dst_env: str,
    dst_password: str,
    *,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> CloneResult:
    """Clone secrets from *src_env* into *dst_env*.

    Parameters
    ----------
    keys:
        If provided, only clone the specified keys.
    overwrite:
        When *True*, existing keys in the destination are replaced.
        When *False* (default), existing keys are left untouched.
    """
    src_secrets = read_secrets(vault_path, src_env, src_password)

    try:
        dst_secrets = read_secrets(vault_path, dst_env, dst_password)
    except Exception:
        dst_secrets = {}

    candidates = {k: v for k, v in src_secrets.items() if keys is None or k in keys}

    if keys:
        missing = set(keys) - set(src_secrets)
        if missing:
            raise KeyError(f"Keys not found in source environment '{src_env}': {sorted(missing)}")

    copied = 0
    skipped = 0
    overwritten = 0

    merged = dict(dst_secrets)
    for key, value in candidates.items():
        if key in dst_secrets:
            if overwrite:
                merged[key] = value
                overwritten += 1
            else:
                skipped += 1
        else:
            merged[key] = value
            copied += 1

    write_secrets(vault_path, dst_env, dst_password, merged)

    return CloneResult(
        source=src_env,
        destination=dst_env,
        copied=copied,
        skipped=skipped,
        overwritten=overwritten,
    )
