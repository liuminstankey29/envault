"""Verify that secrets in an environment match expected checksums or non-empty constraints."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.vault import read_secrets


@dataclass
class VerifyIssue:
    key: str
    reason: str
    severity: str = "error"  # "error" | "warning"


@dataclass
class VerifyResult:
    issues: List[VerifyIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def verify_secrets(
    vault_path: str,
    environment: str,
    password: str,
    *,
    expected_checksums: Optional[Dict[str, str]] = None,
    required_keys: Optional[List[str]] = None,
) -> VerifyResult:
    """Verify secrets against optional checksums and required-key constraints.

    Args:
        vault_path: Path to the vault file.
        environment: Environment name to verify.
        password: Decryption password.
        expected_checksums: Mapping of key -> expected SHA-256 hex digest of value.
        required_keys: Keys that must be present and non-empty.

    Returns:
        VerifyResult with any issues found.
    """
    result = VerifyResult()

    secrets: Dict[str, str] = read_secrets(vault_path, environment, password)

    if required_keys:
        for key in required_keys:
            if key not in secrets:
                result.issues.append(VerifyIssue(key=key, reason="required key is missing"))
            elif not secrets[key].strip():
                result.issues.append(VerifyIssue(key=key, reason="required key is empty"))

    if expected_checksums:
        for key, expected in expected_checksums.items():
            if key not in secrets:
                result.issues.append(VerifyIssue(key=key, reason="key not found for checksum verification"))
                continue
            actual = _sha256(secrets[key])
            if actual != expected.lower():
                result.issues.append(
                    VerifyIssue(key=key, reason=f"checksum mismatch (got {actual[:12]}…, expected {expected[:12]}…)")
                )

    return result


def checksum_of(value: str) -> str:
    """Return the SHA-256 hex digest for *value* (helper for building expected_checksums maps)."""
    return _sha256(value)
