"""Schema validation for environment secrets."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SchemaRule:
    key: str
    required: bool = True
    pattern: Optional[str] = None          # regex the value must match
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[str]] = None


@dataclass
class ValidationIssue:
    key: str
    severity: str   # "error" | "warning"
    message: str


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def validate_secrets(
    secrets: Dict[str, str],
    rules: List[SchemaRule],
) -> ValidationResult:
    """Validate *secrets* against *rules*, returning a ValidationResult."""
    result = ValidationResult()

    for rule in rules:
        value = secrets.get(rule.key)

        if value is None:
            if rule.required:
                result.issues.append(
                    ValidationIssue(rule.key, "error", f"Required key '{rule.key}' is missing.")
                )
            continue

        if rule.min_length is not None and len(value) < rule.min_length:
            result.issues.append(
                ValidationIssue(
                    rule.key, "error",
                    f"Value for '{rule.key}' is too short (min {rule.min_length} chars).",
                )
            )

        if rule.max_length is not None and len(value) > rule.max_length:
            result.issues.append(
                ValidationIssue(
                    rule.key, "error",
                    f"Value for '{rule.key}' is too long (max {rule.max_length} chars).",
                )
            )

        if rule.pattern is not None and not re.fullmatch(rule.pattern, value):
            result.issues.append(
                ValidationIssue(
                    rule.key, "error",
                    f"Value for '{rule.key}' does not match required pattern '{rule.pattern}'.",
                )
            )

        if rule.allowed_values is not None and value not in rule.allowed_values:
            result.issues.append(
                ValidationIssue(
                    rule.key, "error",
                    f"Value for '{rule.key}' must be one of {rule.allowed_values}.",
                )
            )

    return result


def format_validation_results(result: ValidationResult, *, show_ok: bool = True) -> str:
    if result.ok and not result.issues:
        return "All checks passed." if show_ok else ""
    lines = []
    for issue in result.issues:
        prefix = "[ERROR]  " if issue.severity == "error" else "[WARN]   "
        lines.append(f"{prefix}{issue.key}: {issue.message}")
    return "\n".join(lines)
