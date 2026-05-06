"""Vault file read/write operations for envault."""

import json
from pathlib import Path
from typing import Dict

from envault.crypto import encrypt, decrypt

DEFAULT_VAULT_FILE = ".envault"


def _load_raw(vault_path: Path) -> Dict:
    """Load the raw JSON structure from a vault file."""
    if not vault_path.exists():
        return {"environments": {}}
    with vault_path.open("r") as fh:
        return json.load(fh)


def _save_raw(data: Dict, vault_path: Path) -> None:
    """Persist the raw JSON structure to a vault file."""
    with vault_path.open("w") as fh:
        json.dump(data, fh, indent=2)


def write_secrets(
    secrets: Dict[str, str],
    password: str,
    environment: str = "default",
    vault_path: Path = Path(DEFAULT_VAULT_FILE),
) -> None:
    """Encrypt and store secrets for the given environment."""
    data = _load_raw(vault_path)
    plaintext = json.dumps(secrets)
    data["environments"][environment] = encrypt(plaintext, password)
    _save_raw(data, vault_path)


def read_secrets(
    password: str,
    environment: str = "default",
    vault_path: Path = Path(DEFAULT_VAULT_FILE),
) -> Dict[str, str]:
    """Decrypt and return secrets for the given environment.

    Raises:
        KeyError: if the environment does not exist in the vault.
        ValueError: if decryption fails.
    """
    data = _load_raw(vault_path)
    envs = data.get("environments", {})
    if environment not in envs:
        raise KeyError(f"Environment '{environment}' not found in vault.")
    plaintext = decrypt(envs[environment], password)
    return json.loads(plaintext)


def list_environments(
    vault_path: Path = Path(DEFAULT_VAULT_FILE),
) -> list:
    """Return a sorted list of environment names stored in the vault."""
    data = _load_raw(vault_path)
    return sorted(data.get("environments", {}).keys())
