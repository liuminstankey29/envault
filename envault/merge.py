"""Merge secrets from one environment into another."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from envault.vault import read_secrets, write_secrets


@dataclass
class MergeResult:
    added: List[str]
    skipped: List[str]
    overwritten: List[str]


def merge_environments(
    vault_path: str,
    src_env: str,
    src_password: str,
    dst_env: str,
    dst_password: str,
    *,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> MergeResult:
    """Merge secrets from *src_env* into *dst_env*.

    Parameters
    ----------
    keys:
        If given, only these keys are considered; otherwise all keys from
        *src_env* are candidates.
    overwrite:
        When *True*, existing keys in *dst_env* are replaced.  When *False*
        they are skipped.
    """
    src_secrets: Dict[str, str] = read_secrets(vault_path, src_env, src_password)
    dst_secrets: Dict[str, str] = read_secrets(vault_path, dst_env, dst_password)

    candidates = {k: v for k, v in src_secrets.items() if keys is None or k in keys}

    if keys:
        missing = set(keys) - set(src_secrets)
        if missing:
            raise KeyError(f"Keys not found in '{src_env}': {sorted(missing)}")

    added: List[str] = []
    skipped: List[str] = []
    overwritten: List[str] = []

    merged = dict(dst_secrets)
    for key, value in candidates.items():
        if key in dst_secrets:
            if overwrite:
                merged[key] = value
                overwritten.append(key)
            else:
                skipped.append(key)
        else:
            merged[key] = value
            added.append(key)

    write_secrets(vault_path, dst_env, dst_password, merged)
    return MergeResult(added=added, skipped=skipped, overwritten=overwritten)
