"""Tests for envault.expiry_report."""
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from envault.expiry_report import (
    ExpiryReport,
    build_expiry_report,
    format_expiry_report,
)
from envault.ttl import set_expiry
from envault.vault import write_secrets


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "vault.env"
    write_secrets(str(p), "prod", "pass", {"KEY1": "val1", "KEY2": "val2"})
    write_secrets(str(p), "staging", "pass2", {"SKEY": "sval"})
    return str(p)


def _future(days=10):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past(days=1):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def test_empty_report_when_no_ttl(vault_file):
    report = build_expiry_report(vault_file)
    assert report.entries == []


def test_report_includes_future_expiry(vault_file):
    set_expiry(vault_file, "prod", "KEY1", _future(10))
    report = build_expiry_report(vault_file)
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.environment == "prod"
    assert entry.key == "KEY1"
    assert not entry.is_expired
    assert entry.days_remaining is not None
    assert entry.days_remaining > 0


def test_report_marks_past_expiry_as_expired(vault_file):
    set_expiry(vault_file, "prod", "KEY2", _past(1))
    report = build_expiry_report(vault_file)
    assert len(report.entries) == 1
    assert report.entries[0].is_expired
    assert report.entries[0].days_remaining is None


def test_expired_property_filters_correctly(vault_file):
    set_expiry(vault_file, "prod", "KEY1", _future(5))
    set_expiry(vault_file, "prod", "KEY2", _past(1))
    report = build_expiry_report(vault_file)
    assert len(report.expired) == 1
    assert report.expired[0].key == "KEY2"


def test_expiring_soon_within_7_days(vault_file):
    set_expiry(vault_file, "prod", "KEY1", _future(3))
    set_expiry(vault_file, "prod", "KEY2", _future(30))
    report = build_expiry_report(vault_file)
    soon = report.expiring_soon
    assert len(soon) == 1
    assert soon[0].key == "KEY1"


def test_filter_by_environment(vault_file):
    set_expiry(vault_file, "prod", "KEY1", _future(5))
    set_expiry(vault_file, "staging", "SKEY", _future(5))
    report = build_expiry_report(vault_file, environments=["staging"])
    assert all(e.environment == "staging" for e in report.entries)


def test_format_text_no_entries():
    report = ExpiryReport()
    out = format_expiry_report(report, fmt="text")
    assert "No TTL" in out


def test_format_text_shows_environment_and_key(vault_file):
    set_expiry(vault_file, "prod", "KEY1", _future(5))
    report = build_expiry_report(vault_file)
    out = format_expiry_report(report, fmt="text")
    assert "prod" in out
    assert "KEY1" in out


def test_format_json_is_valid_json(vault_file):
    set_expiry(vault_file, "prod", "KEY1", _future(5))
    report = build_expiry_report(vault_file)
    out = format_expiry_report(report, fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["key"] == "KEY1"
    assert data[0]["is_expired"] is False
