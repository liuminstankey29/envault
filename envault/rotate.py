"""Secret rotation: re-encrypt an environment under a new password."""

from __future__ import annotations

from envault.vault import read_secrets, write_secrets


def rotate_environment(
    vault_path: str,
    environment: str,
    old_password: str,
    new_password: str,
) -> int:
    """Re-encrypt all secrets in *environment* with *new_password*.

    Returns the number of secrets that were rotated.
    """
    secrets = read_secrets(vault_path, environment, old_password)
    if not secrets:
        return 0
    write_secrets(vault_path, environment, secrets, new_password)
    return len(secrets)


def rotate_all_environments(
    vault_path: str,
    old_password: str,
    new_password: str,
    environments: list[str],
) -> dict[str, int]:
    """Rotate every listed environment. Returns a mapping of env -> count."""
    results: dict[str, int] = {}
    for env in environments:
        results[env] = rotate_environment(
            vault_path, env, old_password, new_password
        )
    return results
