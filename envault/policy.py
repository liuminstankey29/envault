"""Policy enforcement: define and validate password/secret policies per environment."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class PolicyRule:
    min_length: int = 0
    max_length: Optional[int] = None
    require_uppercase: bool = False
    require_digit: bool = False
    require_special: bool = False
    pattern: Optional[str] = None  # regex the value must match
    forbidden_patterns: List[str] = field(default_factory=list)  # regexes value must NOT match


@dataclass
class PolicyViolation:
    key: str
    rule: str
    message: str


def _policy_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".policy.json")


def load_policy(vault_path: str, environment: str) -> Optional[PolicyRule]:
    path = _policy_path(vault_path)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    env_data = data.get(environment)
    if env_data is None:
        return None
    return PolicyRule(**{k: v for k, v in env_data.items() if k in PolicyRule.__dataclass_fields__})


def save_policy(vault_path: str, environment: str, rule: PolicyRule) -> None:
    path = _policy_path(vault_path)
    data = json.loads(path.read_text()) if path.exists() else {}
    data[environment] = {
        "min_length": rule.min_length,
        "max_length": rule.max_length,
        "require_uppercase": rule.require_uppercase,
        "require_digit": rule.require_digit,
        "require_special": rule.require_special,
        "pattern": rule.pattern,
        "forbidden_patterns": rule.forbidden_patterns,
    }
    path.write_text(json.dumps(data, indent=2))


def enforce_policy(secrets: dict, rule: PolicyRule) -> List[PolicyViolation]:
    violations: List[PolicyViolation] = []
    special_re = re.compile(r"[^A-Za-z0-9]")
    for key, value in secrets.items():
        if not isinstance(value, str):
            continue
        if len(value) < rule.min_length:
            violations.append(PolicyViolation(key, "min_length", f"Value too short (min {rule.min_length})"))
        if rule.max_length is not None and len(value) > rule.max_length:
            violations.append(PolicyViolation(key, "max_length", f"Value too long (max {rule.max_length})"))
        if rule.require_uppercase and not any(c.isupper() for c in value):
            violations.append(PolicyViolation(key, "require_uppercase", "Value must contain an uppercase letter"))
        if rule.require_digit and not any(c.isdigit() for c in value):
            violations.append(PolicyViolation(key, "require_digit", "Value must contain a digit"))
        if rule.require_special and not special_re.search(value):
            violations.append(PolicyViolation(key, "require_special", "Value must contain a special character"))
        if rule.pattern and not re.search(rule.pattern, value):
            violations.append(PolicyViolation(key, "pattern", f"Value does not match required pattern: {rule.pattern}"))
        for fp in rule.forbidden_patterns:
            if re.search(fp, value):
                violations.append(PolicyViolation(key, "forbidden_pattern", f"Value matches forbidden pattern: {fp}"))
    return violations
