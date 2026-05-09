"""Watch a vault environment for changes and trigger a callback or shell command."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

from envault.vault import read_secrets


def _secrets_hash(vault_path: str, environment: str, password: str) -> str:
    """Return a stable hash of the current secrets dict for change detection."""
    try:
        secrets = read_secrets(vault_path, environment, password)
    except Exception:
        secrets = {}
    serialised = json.dumps(secrets, sort_keys=True).encode()
    return hashlib.sha256(serialised).hexdigest()


def watch_environment(
    vault_path: str,
    environment: str,
    password: str,
    *,
    interval: float = 2.0,
    on_change: Optional[Callable[[dict, dict], None]] = None,
    shell_command: Optional[str] = None,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *vault_path/environment* every *interval* seconds.

    When a change is detected:
    - Call *on_change(old_secrets, new_secrets)* if provided.
    - Run *shell_command* via the system shell if provided.

    *max_iterations* is used by tests to bound the loop.
    """
    previous_hash = _secrets_hash(vault_path, environment, password)
    previous_secrets: dict = {}
    try:
        previous_secrets = read_secrets(vault_path, environment, password)
    except Exception:
        pass

    iterations = 0
    while True:
        time.sleep(interval)
        iterations += 1

        current_hash = _secrets_hash(vault_path, environment, password)
        if current_hash != previous_hash:
            try:
                current_secrets = read_secrets(vault_path, environment, password)
            except Exception:
                current_secrets = {}

            if on_change is not None:
                on_change(previous_secrets, current_secrets)

            if shell_command is not None:
                subprocess.run(shell_command, shell=True, check=False)

            previous_secrets = current_secrets
            previous_hash = current_hash

        if max_iterations is not None and iterations >= max_iterations:
            break
