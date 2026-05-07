"""Lint secrets in a vault environment for common issues."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.vault import read_secrets


@dataclass
class LintIssue:
    key: str
    severity: str  # 'error' | 'warning' | 'info'
    message: str


# Patterns that suggest a secret is a placeholder / not real
_PLACEHOLDER_RE = re.compile(
    r'^(todo|fixme|changeme|replace_?me|placeholder|example|your[_-]?.*here|xxx+|tbd|none|null|empty)$',
    re.IGNORECASE,
)

_VALID_KEY_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')


def lint_secrets(
    vault_path: str,
    env: str,
    password: str,
    *,
    min_value_length: int = 1,
) -> List[LintIssue]:
    """Return a list of LintIssue for every problem found in *env*."""
    secrets: Dict[str, str] = read_secrets(vault_path, env, password)
    issues: List[LintIssue] = []

    for key, value in secrets.items():
        # Key naming convention
        if not _VALID_KEY_RE.match(key):
            issues.append(LintIssue(key, 'warning',
                                    'Key should be UPPER_SNAKE_CASE'))

        # Empty value
        if len(value) < min_value_length:
            issues.append(LintIssue(key, 'error',
                                    f'Value is empty or shorter than {min_value_length} character(s)'))
            continue

        # Placeholder value
        if _PLACEHOLDER_RE.match(value.strip()):
            issues.append(LintIssue(key, 'error',
                                    f'Value looks like a placeholder: {value!r}'))

        # Whitespace padding
        if value != value.strip():
            issues.append(LintIssue(key, 'warning',
                                    'Value has leading or trailing whitespace'))

    return issues


def format_lint_results(issues: List[LintIssue], *, use_color: bool = False) -> str:
    if not issues:
        return 'No issues found.'
    lines = []
    icons = {'error': '[ERROR]', 'warning': '[WARN] ', 'info': '[INFO] '}
    for issue in issues:
        tag = icons.get(issue.severity, '[?]    ')
        lines.append(f'{tag} {issue.key}: {issue.message}')
    return '\n'.join(lines)
