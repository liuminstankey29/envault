"""Compare secrets between two environments or two vault files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.vault import read_secrets


@dataclass
class CompareResult:
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)
    same_keys: List[str] = field(default_factory=list)
    different_keys: List[str] = field(default_factory=list)

    @property
    def is_identical(self) -> bool:
        return not (self.only_in_a or self.only_in_b or self.different_keys)


def compare_environments(
    vault_path: str,
    env_a: str,
    password_a: str,
    env_b: str,
    password_b: Optional[str] = None,
    vault_path_b: Optional[str] = None,
) -> CompareResult:
    """Compare secrets between env_a and env_b.

    If vault_path_b is given, env_b is read from that vault instead.
    If password_b is None, password_a is reused.
    """
    secrets_a: Dict[str, str] = read_secrets(vault_path, env_a, password_a)
    effective_vault_b = vault_path_b or vault_path
    effective_pass_b = password_b if password_b is not None else password_a
    secrets_b: Dict[str, str] = read_secrets(effective_vault_b, env_b, effective_pass_b)

    keys_a = set(secrets_a)
    keys_b = set(secrets_b)

    result = CompareResult(
        only_in_a=sorted(keys_a - keys_b),
        only_in_b=sorted(keys_b - keys_a),
    )

    for key in sorted(keys_a & keys_b):
        if secrets_a[key] == secrets_b[key]:
            result.same_keys.append(key)
        else:
            result.different_keys.append(key)

    return result


def format_compare_result(
    result: CompareResult,
    env_a: str,
    env_b: str,
    show_counts: bool = True,
) -> str:
    lines: List[str] = []

    if result.only_in_a:
        lines.append(f"Only in [{env_a}]:")
        for k in result.only_in_a:
            lines.append(f"  - {k}")

    if result.only_in_b:
        lines.append(f"Only in [{env_b}]:")
        for k in result.only_in_b:
            lines.append(f"  + {k}")

    if result.different_keys:
        lines.append("Different values:")
        for k in result.different_keys:
            lines.append(f"  ~ {k}")

    if show_counts:
        lines.append(
            f"Summary: {len(result.same_keys)} identical, "
            f"{len(result.different_keys)} different, "
            f"{len(result.only_in_a)} only in {env_a}, "
            f"{len(result.only_in_b)} only in {env_b}."
        )

    if result.is_identical:
        lines.append(f"Environments [{env_a}] and [{env_b}] are identical.")

    return "\n".join(lines)
