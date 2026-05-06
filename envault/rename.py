"""Rename a secret key within an environment or across environments."""

from envault.vault import read_secrets, write_secrets


def rename_secret(
    vault_path: str,
    env: str,
    old_key: str,
    new_key: str,
    password: str,
    overwrite: bool = False,
) -> dict:
    """
    Rename *old_key* to *new_key* inside *env*.

    Returns a result dict with keys:
        - renamed (bool): True if the rename was performed.
        - skipped (bool): True if new_key already existed and overwrite=False.
        - old_key (str)
        - new_key (str)
    """
    secrets = read_secrets(vault_path, env, password)

    if old_key not in secrets:
        raise KeyError(f"Key '{old_key}' not found in environment '{env}'.")

    if new_key in secrets and not overwrite:
        return {"renamed": False, "skipped": True, "old_key": old_key, "new_key": new_key}

    value = secrets.pop(old_key)
    secrets[new_key] = value
    write_secrets(vault_path, env, password, secrets)

    return {"renamed": True, "skipped": False, "old_key": old_key, "new_key": new_key}


def rename_secret_across_environments(
    vault_path: str,
    old_key: str,
    new_key: str,
    password: str,
    overwrite: bool = False,
) -> list:
    """
    Rename *old_key* to *new_key* in every environment that contains it.

    Returns a list of result dicts (one per environment touched).
    """
    from envault.vault import list_environments

    results = []
    for env in list_environments(vault_path):
        secrets = read_secrets(vault_path, env, password)
        if old_key not in secrets:
            continue
        result = rename_secret(vault_path, env, old_key, new_key, password, overwrite=overwrite)
        result["env"] = env
        results.append(result)
    return results
