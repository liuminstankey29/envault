"""Mirror secrets from one vault file to another (cross-vault sync)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import read_secrets, write_secrets


@dataclass
class MirrorResult:
    environment: str
    source_vault: str
    dest_vault: str
    copied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.copied) + len(self.overwritten)


def mirror_environment(
    src_vault: Path,
    src_password: str,
    dest_vault: Path,
    dest_password: str,
    environment: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> MirrorResult:
    """Copy secrets for *environment* from src_vault into dest_vault.

    Parameters
    ----------
    src_vault:    Path to the source vault file.
    src_password: Master password for the source vault.
    dest_vault:   Path to the destination vault file.
    dest_password: Master password for the destination vault.
    environment:  Environment name to mirror.
    keys:         Optional allowlist of secret keys to mirror.
    overwrite:    When True, existing keys in the destination are replaced.
    """
    result = MirrorResult(
        environment=environment,
        source_vault=str(src_vault),
        dest_vault=str(dest_vault),
    )

    src_secrets = read_secrets(src_vault, src_password, environment)
    if keys:
        src_secrets = {k: v for k, v in src_secrets.items() if k in keys}

    try:
        dest_secrets = read_secrets(dest_vault, dest_password, environment)
    except (FileNotFoundError, KeyError):
        dest_secrets = {}

    merged: dict[str, str] = dict(dest_secrets)

    for key, value in src_secrets.items():
        if key in dest_secrets:
            if overwrite:
                merged[key] = value
                result.overwritten.append(key)
            else:
                result.skipped.append(key)
        else:
            merged[key] = value
            result.copied.append(key)

    write_secrets(dest_vault, dest_password, environment, merged)
    return result
