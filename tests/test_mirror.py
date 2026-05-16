"""Tests for envault.mirror."""

from __future__ import annotations

import pytest

from envault.mirror import mirror_environment
from envault.vault import read_secrets, write_secrets


@pytest.fixture()
def two_vaults(tmp_path):
    src = tmp_path / "src.vault"
    dst = tmp_path / "dst.vault"
    write_secrets(src, "srcpass", "prod", {"KEY1": "val1", "KEY2": "val2", "KEY3": "val3"})
    write_secrets(dst, "dstpass", "prod", {"KEY2": "old2"})
    return src, dst


def test_mirror_copies_new_keys(two_vaults):
    src, dst = two_vaults
    result = mirror_environment(src, "srcpass", dst, "dstpass", "prod")
    assert "KEY1" in result.copied
    assert "KEY3" in result.copied


def test_mirror_skips_existing_by_default(two_vaults):
    src, dst = two_vaults
    result = mirror_environment(src, "srcpass", dst, "dstpass", "prod")
    assert "KEY2" in result.skipped
    dest_secrets = read_secrets(dst, "dstpass", "prod")
    assert dest_secrets["KEY2"] == "old2"  # unchanged


def test_mirror_overwrite_replaces_existing(two_vaults):
    src, dst = two_vaults
    result = mirror_environment(src, "srcpass", dst, "dstpass", "prod", overwrite=True)
    assert "KEY2" in result.overwritten
    dest_secrets = read_secrets(dst, "dstpass", "prod")
    assert dest_secrets["KEY2"] == "val2"


def test_mirror_keys_filter(two_vaults):
    src, dst = two_vaults
    result = mirror_environment(src, "srcpass", dst, "dstpass", "prod", keys=["KEY1"])
    assert result.copied == ["KEY1"]
    dest_secrets = read_secrets(dst, "dstpass", "prod")
    assert "KEY3" not in dest_secrets


def test_mirror_creates_dest_env_if_missing(tmp_path):
    src = tmp_path / "src.vault"
    dst = tmp_path / "dst.vault"
    write_secrets(src, "srcpass", "staging", {"FOO": "bar"})
    result = mirror_environment(src, "srcpass", dst, "dstpass", "staging")
    assert result.copied == ["FOO"]
    assert read_secrets(dst, "dstpass", "staging") == {"FOO": "bar"}


def test_mirror_total_counts_copied_and_overwritten(two_vaults):
    src, dst = two_vaults
    result = mirror_environment(src, "srcpass", dst, "dstpass", "prod", overwrite=True)
    assert result.total == len(result.copied) + len(result.overwritten)


def test_mirror_result_records_vault_paths(two_vaults):
    src, dst = two_vaults
    result = mirror_environment(src, "srcpass", dst, "dstpass", "prod")
    assert result.source_vault == str(src)
    assert result.dest_vault == str(dst)
    assert result.environment == "prod"
