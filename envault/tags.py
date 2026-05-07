"""Tag management for envault secrets — assign and filter secrets by tag."""

from __future__ import annotations

from typing import Dict, List, Optional

from envault.vault import read_secrets, write_secrets

TAGS_KEY = "__tags__"


def _get_tags_map(vault_path: str, environment: str, password: str) -> Dict[str, List[str]]:
    """Return the tags mapping {secret_key: [tag, ...]} for an environment."""
    secrets = read_secrets(vault_path, environment, password)
    raw = secrets.get(TAGS_KEY, "")
    if not raw:
        return {}
    import json
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _save_tags_map(
    vault_path: str,
    environment: str,
    password: str,
    tags_map: Dict[str, List[str]],
) -> None:
    import json
    secrets = read_secrets(vault_path, environment, password)
    secrets[TAGS_KEY] = json.dumps(tags_map)
    write_secrets(vault_path, environment, password, secrets)


def add_tag(vault_path: str, environment: str, password: str, key: str, tag: str) -> None:
    """Add *tag* to *key* in *environment*. Idempotent."""
    secrets = read_secrets(vault_path, environment, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in environment '{environment}'.")
    tags_map = _get_tags_map(vault_path, environment, password)
    tags = tags_map.get(key, [])
    if tag not in tags:
        tags.append(tag)
    tags_map[key] = tags
    _save_tags_map(vault_path, environment, password, tags_map)


def remove_tag(vault_path: str, environment: str, password: str, key: str, tag: str) -> bool:
    """Remove *tag* from *key*. Returns True if the tag was present."""
    tags_map = _get_tags_map(vault_path, environment, password)
    tags = tags_map.get(key, [])
    if tag not in tags:
        return False
    tags.remove(tag)
    tags_map[key] = tags
    _save_tags_map(vault_path, environment, password, tags_map)
    return True


def list_tags(vault_path: str, environment: str, password: str, key: str) -> List[str]:
    """Return the list of tags for *key* in *environment*."""
    tags_map = _get_tags_map(vault_path, environment, password)
    return tags_map.get(key, [])


def filter_by_tag(
    vault_path: str,
    environment: str,
    password: str,
    tag: str,
    include_meta: bool = False,
) -> Dict[str, str]:
    """Return secrets in *environment* that carry *tag*."""
    secrets = read_secrets(vault_path, environment, password)
    tags_map = _get_tags_map(vault_path, environment, password)
    result = {}
    for key, value in secrets.items():
        if not include_meta and key == TAGS_KEY:
            continue
        if tag in tags_map.get(key, []):
            result[key] = value
    return result
