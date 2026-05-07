"""Snapshot support: capture and restore environment state."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import read_secrets, write_secrets


def _snapshot_dir(vault_path: str) -> Path:
    base = Path(vault_path).parent
    d = base / ".envault_snapshots"
    d.mkdir(exist_ok=True)
    return d


def _snapshot_path(vault_path: str, name: str) -> Path:
    return _snapshot_dir(vault_path) / f"{name}.json"


def create_snapshot(
    vault_path: str,
    password: str,
    environment: str,
    name: Optional[str] = None,
) -> str:
    """Capture current secrets for *environment* and save as a named snapshot.

    Returns the snapshot name used.
    """
    secrets = read_secrets(vault_path, password, environment)
    if name is None:
        name = f"{environment}_{int(time.time())}"
    payload = {
        "environment": environment,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "secrets": secrets,
    }
    path = _snapshot_path(vault_path, name)
    path.write_text(json.dumps(payload, indent=2))
    return name


def restore_snapshot(
    vault_path: str,
    password: str,
    name: str,
    environment: Optional[str] = None,
) -> int:
    """Restore secrets from *name* into *environment* (defaults to original env).

    Returns the number of secrets restored.
    """
    path = _snapshot_path(vault_path, name)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot '{name}' not found.")
    payload = json.loads(path.read_text())
    target_env = environment or payload["environment"]
    secrets: Dict[str, str] = payload["secrets"]
    write_secrets(vault_path, password, target_env, secrets)
    return len(secrets)


def list_snapshots(vault_path: str) -> List[Dict[str, str]]:
    """Return metadata for all snapshots, sorted newest-first."""
    snap_dir = _snapshot_dir(vault_path)
    results = []
    for p in sorted(snap_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            data = json.loads(p.read_text())
            results.append({
                "name": p.stem,
                "environment": data.get("environment", ""),
                "created_at": data.get("created_at", ""),
                "key_count": str(len(data.get("secrets", {}))),
            })
        except (json.JSONDecodeError, KeyError):
            pass
    return results


def delete_snapshot(vault_path: str, name: str) -> bool:
    """Delete a snapshot by name. Returns True if it existed."""
    path = _snapshot_path(vault_path, name)
    if path.exists():
        path.unlink()
        return True
    return False
