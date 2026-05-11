"""Archive and restore entire vault environments as portable encrypted bundles."""

from __future__ import annotations

import json
import os
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import read_secrets, write_secrets


@dataclass
class ArchiveResult:
    environment: str
    key_count: int
    archive_path: str


@dataclass
class RestoreResult:
    environment: str
    keys_written: int
    keys_skipped: int
    skipped: List[str] = field(default_factory=list)


def archive_environment(
    vault_path: str,
    environment: str,
    password: str,
    output_path: str,
    label: Optional[str] = None,
) -> ArchiveResult:
    """Export an environment's secrets into a compressed encrypted-bundle file."""
    secrets = read_secrets(vault_path, environment, password)

    meta = {
        "environment": environment,
        "label": label or "",
        "key_count": len(secrets),
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        secrets_file = os.path.join(tmpdir, "secrets.json")
        meta_file = os.path.join(tmpdir, "meta.json")

        with open(secrets_file, "w") as fh:
            json.dump(secrets, fh)
        with open(meta_file, "w") as fh:
            json.dump(meta, fh)

        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(secrets_file, arcname="secrets.json")
            tar.add(meta_file, arcname="meta.json")

    return ArchiveResult(
        environment=environment,
        key_count=len(secrets),
        archive_path=output_path,
    )


def restore_environment(
    vault_path: str,
    archive_path: str,
    password: str,
    overwrite: bool = False,
    target_environment: Optional[str] = None,
) -> RestoreResult:
    """Restore secrets from an archive bundle into a vault environment."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(tmpdir)

        with open(os.path.join(tmpdir, "meta.json")) as fh:
            meta = json.load(fh)
        with open(os.path.join(tmpdir, "secrets.json")) as fh:
            incoming: dict = json.load(fh)

    environment = target_environment or meta["environment"]

    try:
        existing = read_secrets(vault_path, environment, password)
    except Exception:
        existing = {}

    to_write = {}
    skipped = []
    for key, value in incoming.items():
        if key in existing and not overwrite:
            skipped.append(key)
        else:
            to_write[key] = value

    if to_write:
        merged = {**existing, **to_write}
        write_secrets(vault_path, environment, password, merged)

    return RestoreResult(
        environment=environment,
        keys_written=len(to_write),
        keys_skipped=len(skipped),
        skipped=skipped,
    )
