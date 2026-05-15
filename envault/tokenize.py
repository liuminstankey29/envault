"""Tokenize secrets: generate opaque tokens that map to real secret values."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _token_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".tokens.json")


def _load_token_map(vault_path: str) -> dict:
    p = _token_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_token_map(vault_path: str, data: dict) -> None:
    _token_path(vault_path).write_text(json.dumps(data, indent=2))


def _make_token() -> str:
    return "tok_" + secrets.token_hex(20)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass
class TokenizeResult:
    token: str
    environment: str
    key: str
    created: bool  # True if new, False if token already existed


def create_token(vault_path: str, environment: str, key: str) -> TokenizeResult:
    """Create (or retrieve existing) an opaque token for a secret key."""
    data = _load_token_map(vault_path)
    env_map = data.setdefault(environment, {})

    if key in env_map:
        return TokenizeResult(
            token=env_map[key]["token"],
            environment=environment,
            key=key,
            created=False,
        )

    token = _make_token()
    env_map[key] = {"token": token, "hash": _hash_token(token)}
    _save_token_map(vault_path, data)
    return TokenizeResult(token=token, environment=environment, key=key, created=True)


def resolve_token(vault_path: str, token: str) -> Optional[tuple[str, str]]:
    """Resolve a token back to (environment, key). Returns None if not found."""
    data = _load_token_map(vault_path)
    for env, keys in data.items():
        for key, entry in keys.items():
            if entry.get("token") == token:
                return env, key
    return None


def revoke_token(vault_path: str, environment: str, key: str) -> bool:
    """Remove the token for a given key. Returns True if it existed."""
    data = _load_token_map(vault_path)
    env_map = data.get(environment, {})
    if key not in env_map:
        return False
    del env_map[key]
    if not env_map:
        data.pop(environment, None)
    _save_token_map(vault_path, data)
    return True


def list_tokens(vault_path: str, environment: str) -> dict[str, str]:
    """Return {key: token} mapping for an environment."""
    data = _load_token_map(vault_path)
    return {k: v["token"] for k, v in data.get(environment, {}).items()}
