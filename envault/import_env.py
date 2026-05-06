"""Import secrets from existing .env files or JSON into a vault environment."""

import json
import os
import re
from typing import Dict, Optional, Tuple


def parse_dotenv(content: str) -> Dict[str, str]:
    """Parse a .env file content into a key-value dictionary."""
    result = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        # Strip optional surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
            if value[0] == '"':
                value = value.replace('\\"', '"').replace('\\n', '\n')
        result[key] = value
    return result


def parse_json_env(content: str) -> Dict[str, str]:
    """Parse a JSON object of string key-value pairs."""
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("JSON input must be a top-level object")
    return {str(k): str(v) for k, v in data.items()}


def load_import_file(path: str) -> Tuple[Dict[str, str], str]:
    """Load secrets from a .env or .json file. Returns (secrets, format)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Import file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    if path.endswith(".json"):
        return parse_json_env(content), "json"
    return parse_dotenv(content), "dotenv"


def import_secrets(
    vault_path: str,
    environment: str,
    password: str,
    import_path: str,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Import secrets from a file into a vault environment.

    Returns the dict of keys that were actually written.
    """
    from envault.vault import read_secrets, write_secrets

    incoming, _ = load_import_file(import_path)
    if not incoming:
        return {}

    try:
        existing = read_secrets(vault_path, environment, password)
    except (FileNotFoundError, KeyError):
        existing = {}

    to_write = {}
    for k, v in incoming.items():
        if overwrite or k not in existing:
            to_write[k] = v

    if to_write:
        merged = {**existing, **to_write}
        write_secrets(vault_path, environment, password, merged)

    return to_write
