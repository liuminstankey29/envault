"""Tests for envault.gc and envault.cli_gc."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from envault.vault import write_secrets
from envault.gc import gc_sidecar_files, GCResult


@pytest.fixture()
def vault_file(tmp_path):
    vf = tmp_path / "test.vault"
    write_secrets(vf, "dev", "pass", {"KEY": "val"})
    return vf


def _write_sidecar(vault_path: Path, suffix: str, data: dict) -> Path:
    p = vault_path.with_suffix(suffix)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def _write_jsonl_sidecar(vault_path: Path, suffix: str, rows: list) -> Path:
    p = vault_path.with_suffix(suffix)
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def test_no_sidecars_returns_empty_result(vault_file):
    result = gc_sidecar_files(vault_file, "pass")
    assert isinstance(result, GCResult)
    assert result.total_removed == 0
    assert result.total_files_cleaned == 0


def test_live_environment_entry_kept(vault_file):
    _write_sidecar(vault_file, ".ttl.json", {"dev": {"KEY": "2099-01-01T00:00:00"}})
    result = gc_sidecar_files(vault_file, "pass")
    assert result.total_removed == 0


def test_orphaned_environment_entry_removed(vault_file):
    sidecar = _write_sidecar(
        vault_file, ".ttl.json",
        {"dev": {"KEY": "2099-01-01"}, "ghost": {"KEY": "2099-01-01"}},
    )
    result = gc_sidecar_files(vault_file, "pass")
    assert result.total_removed == 1
    assert any("ghost" in k for k in result.removed_keys)
    remaining = json.loads(sidecar.read_text())
    assert "ghost" not in remaining
    assert "dev" in remaining


def test_dry_run_does_not_modify_file(vault_file):
    sidecar = _write_sidecar(
        vault_file, ".lock.json",
        {"ghost": {"locked": True}},
    )
    original = sidecar.read_text()
    result = gc_sidecar_files(vault_file, "pass", dry_run=True)
    assert result.total_removed == 1
    assert sidecar.read_text() == original


def test_jsonl_sidecar_orphan_removed(vault_file):
    sidecar = _write_jsonl_sidecar(
        vault_file, ".audit.jsonl",
        [
            {"environment": "dev", "action": "set", "key": "K"},
            {"environment": "ghost", "action": "set", "key": "X"},
        ],
    )
    result = gc_sidecar_files(vault_file, "pass")
    assert result.total_removed == 1
    lines = [l for l in sidecar.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0])["environment"] == "dev"


def test_multiple_sidecars_cleaned(vault_file):
    _write_sidecar(vault_file, ".ttl.json", {"ghost": {}})
    _write_sidecar(vault_file, ".lock.json", {"ghost": {}})
    result = gc_sidecar_files(vault_file, "pass")
    assert result.total_files_cleaned == 2
    assert result.total_removed == 2


def test_bad_password_returns_empty_result(vault_file):
    _write_sidecar(vault_file, ".ttl.json", {"ghost": {}})
    result = gc_sidecar_files(vault_file, "wrong-password")
    # live envs cannot be determined; nothing is removed to avoid data loss
    assert result.total_removed == 0
