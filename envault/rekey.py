"""Re-encrypt all secrets in an environment under a new password."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from envault.vault import read_secrets, write_secrets, list_environments


@dataclass
class RekeyResult:
    environment: str
    secrets_rekeyed: int
    skipped: bool = False
    skip_reason: str = ""

    @property
    def total(self) -> int:
        return self.secrets_rekeyed


def rekey_environment(
    vault_path: Path,
    environment: str,
    old_password: str,
    new_password: str,
) -> RekeyResult:
    """Re-encrypt a single environment's secrets with *new_password*.

    Raises ValueError if *old_password* is wrong (propagated from decrypt).
    """
    secrets = read_secrets(vault_path, environment, old_password)
    write_secrets(vault_path, environment, new_password, secrets)
    return RekeyResult(environment=environment, secrets_rekeyed=len(secrets))


def rekey_all_environments(
    vault_path: Path,
    old_password: str,
    new_password: str,
    *,
    skip_errors: bool = False,
) -> list[RekeyResult]:
    """Re-encrypt every environment in the vault.

    If *skip_errors* is True, environments whose old password doesn't match
    are recorded as skipped rather than raising.
    """
    results: list[RekeyResult] = []
    for env in list_environments(vault_path):
        try:
            result = rekey_environment(vault_path, env, old_password, new_password)
        except Exception as exc:  # noqa: BLE001
            if not skip_errors:
                raise
            results.append(
                RekeyResult(
                    environment=env,
                    secrets_rekeyed=0,
                    skipped=True,
                    skip_reason=str(exc),
                )
            )
        else:
            results.append(result)
    return results
