"""Promote secrets from one environment to another."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from envault.vault import read_secrets, write_secrets


@dataclass
class PromoteResult:
    promoted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.promoted) + len(self.overwritten)


def _env_exists(vault_path: str, env: str, password: str) -> bool:
    try:
        read_secrets(vault_path, env, password)
        return True
    except Exception:
        return False


def promote_secrets(
    vault_path: str,
    src_env: str,
    dst_env: str,
    src_password: str,
    dst_password: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> PromoteResult:
    """Copy secrets from src_env to dst_env, optionally overwriting."""
    src = read_secrets(vault_path, src_env, src_password)
    dst = read_secrets(vault_path, dst_env, dst_password) if _env_exists(vault_path, dst_env, dst_password) else {}

    candidates = keys if keys is not None else list(src.keys())
    result = PromoteResult()

    for key in candidates:
        if key not in src:
            raise KeyError(f"Key {key!r} not found in source environment {src_env!r}")
        if key in dst and not overwrite:
            result.skipped.append(key)
            continue
        if key in dst and overwrite:
            result.overwritten.append(key)
        else:
            result.promoted.append(key)
        dst[key] = src[key]

    write_secrets(vault_path, dst_env, dst_password, dst)
    return result
