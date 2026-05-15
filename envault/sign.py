"""HMAC-based signing and verification of environment secret bundles."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envault.vault import read_secrets

_SIGN_SUFFIX = ".sigs.json"


def _sign_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix("").parent / (Path(vault_path).stem + _SIGN_SUFFIX)


def _load_sig_map(vault_path: str) -> dict:
    p = _sign_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_sig_map(vault_path: str, data: dict) -> None:
    _sign_path(vault_path).write_text(json.dumps(data, indent=2))


def _compute_sig(secrets: dict, signing_key: str) -> str:
    """Return a hex HMAC-SHA256 digest of the canonical JSON of *secrets*."""
    payload = json.dumps(secrets, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(signing_key.encode(), payload, hashlib.sha256).hexdigest()


@dataclass
class SignResult:
    environment: str
    signature: str
    updated: bool


@dataclass
class VerifySignResult:
    environment: str
    valid: bool
    expected: Optional[str]
    actual: Optional[str]


def sign_environment(vault_path: str, environment: str, password: str, signing_key: str) -> SignResult:
    """Compute and store an HMAC signature for *environment*."""
    secrets = read_secrets(vault_path, environment, password)
    sig = _compute_sig(secrets, signing_key)
    sigs = _load_sig_map(vault_path)
    updated = sigs.get(environment) != sig
    sigs[environment] = sig
    _save_sig_map(vault_path, sigs)
    return SignResult(environment=environment, signature=sig, updated=updated)


def verify_environment(vault_path: str, environment: str, password: str, signing_key: str) -> VerifySignResult:
    """Verify the stored signature for *environment* against current secrets."""
    sigs = _load_sig_map(vault_path)
    stored = sigs.get(environment)
    if stored is None:
        return VerifySignResult(environment=environment, valid=False, expected=None, actual=None)
    secrets = read_secrets(vault_path, environment, password)
    actual = _compute_sig(secrets, signing_key)
    return VerifySignResult(environment=environment, valid=hmac.compare_digest(stored, actual),
                            expected=stored, actual=actual)


def list_signed_environments(vault_path: str) -> list[str]:
    """Return environments that have a stored signature."""
    return list(_load_sig_map(vault_path).keys())
