"""Generate a full health report for an envault vault."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import list_environments, read_secrets
from envault.lint import lint_secrets
from envault.ttl import get_expiry, is_expired
from envault.lock import is_locked
from envault.quota import get_quota_status


@dataclass
class EnvironmentReport:
    environment: str
    secret_count: int
    locked: bool
    lint_errors: int
    lint_warnings: int
    expired_keys: List[str] = field(default_factory=list)
    quota_pct: Optional[float] = None


@dataclass
class VaultReport:
    vault_path: str
    environments: List[EnvironmentReport] = field(default_factory=list)

    @property
    def total_secrets(self) -> int:
        return sum(e.secret_count for e in self.environments)

    @property
    def total_errors(self) -> int:
        return sum(e.lint_errors for e in self.environments)

    @property
    def total_warnings(self) -> int:
        return sum(e.lint_warnings for e in self.environments)


def build_environment_report(
    vault_path: Path,
    environment: str,
    password: str,
) -> EnvironmentReport:
    try:
        secrets = read_secrets(vault_path, environment, password)
    except Exception:
        return EnvironmentReport(
            environment=environment,
            secret_count=0,
            locked=is_locked(vault_path, environment),
            lint_errors=0,
            lint_warnings=0,
        )

    issues = lint_secrets(vault_path, environment, password)
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")

    expired = [
        k for k in secrets
        if get_expiry(vault_path, environment, k) is not None
        and is_expired(vault_path, environment, k)
    ]

    qs = get_quota_status(vault_path, environment)
    quota_pct = None
    if qs is not None and qs.limit > 0:
        quota_pct = round(qs.used / qs.limit * 100, 1)

    return EnvironmentReport(
        environment=environment,
        secret_count=len(secrets),
        locked=is_locked(vault_path, environment),
        lint_errors=errors,
        lint_warnings=warnings,
        expired_keys=expired,
        quota_pct=quota_pct,
    )


def build_vault_report(
    vault_path: Path,
    passwords: dict,  # {env: password}
) -> VaultReport:
    envs = list_environments(vault_path)
    report = VaultReport(vault_path=str(vault_path))
    for env in envs:
        pw = passwords.get(env, "")
        report.environments.append(
            build_environment_report(vault_path, env, pw)
        )
    return report
