"""Tests for envault.quota."""
from __future__ import annotations

import pytest

from envault.vault import write_secrets
from envault.quota import (
    QuotaStatus,
    check_quota,
    get_quota_status,
    list_quotas,
    remove_quota,
    set_quota,
)


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "vault.env"
    write_secrets(str(p), "dev", "pass", {"KEY1": "v1", "KEY2": "v2"})
    return str(p)


def test_set_quota_persists(vault_file):
    set_quota(vault_file, "dev", 10)
    quotas = list_quotas(vault_file)
    assert quotas["dev"] == 10


def test_set_quota_invalid_raises(vault_file):
    with pytest.raises(ValueError):
        set_quota(vault_file, "dev", 0)


def test_remove_quota_returns_true_when_existed(vault_file):
    set_quota(vault_file, "dev", 5)
    assert remove_quota(vault_file, "dev") is True


def test_remove_quota_returns_false_when_not_set(vault_file):
    assert remove_quota(vault_file, "staging") is False


def test_remove_quota_clears_entry(vault_file):
    set_quota(vault_file, "dev", 5)
    remove_quota(vault_file, "dev")
    assert "dev" not in list_quotas(vault_file)


def test_get_quota_status_used_count(vault_file):
    set_quota(vault_file, "dev", 10)
    status = get_quota_status(vault_file, "dev", "pass")
    assert status.used == 2
    assert status.limit == 10
    assert status.exceeded is False


def test_quota_status_exceeded(vault_file):
    set_quota(vault_file, "dev", 1)
    status = get_quota_status(vault_file, "dev", "pass")
    assert status.exceeded is True


def test_quota_status_available(vault_file):
    set_quota(vault_file, "dev", 5)
    status = get_quota_status(vault_file, "dev", "pass")
    assert status.available == 3


def test_quota_status_no_limit_returns_none_available(vault_file):
    status = get_quota_status(vault_file, "dev", "pass")
    assert status.limit is None
    assert status.available is None
    assert status.exceeded is False


def test_check_quota_passes_when_within_limit(vault_file):
    set_quota(vault_file, "dev", 5)
    status = check_quota(vault_file, "dev", "pass")
    assert isinstance(status, QuotaStatus)


def test_check_quota_raises_when_exceeded(vault_file):
    set_quota(vault_file, "dev", 1)
    with pytest.raises(RuntimeError, match="Quota exceeded"):
        check_quota(vault_file, "dev", "pass")


def test_list_quotas_multiple_environments(vault_file):
    set_quota(vault_file, "dev", 10)
    set_quota(vault_file, "prod", 50)
    quotas = list_quotas(vault_file)
    assert quotas == {"dev": 10, "prod": 50}


def test_list_quotas_empty_when_none_set(vault_file):
    assert list_quotas(vault_file) == {}
