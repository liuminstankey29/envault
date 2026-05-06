"""Copy secrets between environments within the same vault."""

from __future__ import annotations

from typing import Optional

from envault.vault import read_secrets, write_secrets


def copy_secrets(
    vault_path: str,
    src_env: str,
    dst_env: str,
    src_password: str,
    dst_password: str,
    keys: Optional[list[str]] = None,
    overwrite: bool = True,
) -> dict[str, int]:
    """Copy secrets from *src_env* into *dst_env*.

    Args:
        vault_path: Path to the vault file.
        src_env: Source environment name.
        dst_env: Destination environment name.
        src_password: Password for the source environment.
        dst_password: Password for the destination environment.
        keys: Optional list of keys to copy. Copies all if *None*.
        overwrite: When *False*, skip keys that already exist in dst.

    Returns:
        A dict with ``copied`` and ``skipped`` counts.
    """
    src_secrets = read_secrets(vault_path, src_env, src_password)

    if keys is not None:
        missing = set(keys) - src_secrets.keys()
        if missing:
            raise KeyError(f"Keys not found in '{src_env}': {sorted(missing)}")
        src_secrets = {k: v for k, v in src_secrets.items() if k in keys}

    try:
        dst_secrets = read_secrets(vault_path, dst_env, dst_password)
    except Exception:
        dst_secrets = {}

    copied = 0
    skipped = 0
    for key, value in src_secrets.items():
        if not overwrite and key in dst_secrets:
            skipped += 1
            continue
        dst_secrets[key] = value
        copied += 1

    if copied:
        write_secrets(vault_path, dst_env, dst_password, dst_secrets)

    return {"copied": copied, "skipped": skipped}
