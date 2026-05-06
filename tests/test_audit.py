"""Tests for envault.audit and envault.cli_audit."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from envault.audit import record_event, read_events, filter_events


@pytest.fixture
def log_file(tmp_path):
    return str(tmp_path / "audit.jsonl")


def test_record_event_creates_file(log_file):
    record_event("set", "production", key="DB_URL", log_path=log_file)
    assert Path(log_file).exists()


def test_record_event_returns_dict(log_file):
    event = record_event("get", "staging", key="API_KEY", log_path=log_file)
    assert event["action"] == "get"
    assert event["environment"] == "staging"
    assert event["key"] == "API_KEY"
    assert "timestamp" in event


def test_multiple_events_appended(log_file):
    record_event("set", "dev", key="FOO", log_path=log_file)
    record_event("set", "dev", key="BAR", log_path=log_file)
    events = read_events(log_path=log_file)
    assert len(events) == 2


def test_read_events_empty_when_no_file(tmp_path):
    events = read_events(log_path=str(tmp_path / "nonexistent.jsonl"))
    assert events == []


def test_event_without_key(log_file):
    event = record_event("rotate", "production", log_path=log_file)
    assert "key" not in event


def test_extra_fields_stored(log_file):
    record_event("export", "staging", extra={"format": "dotenv"}, log_path=log_file)
    events = read_events(log_path=log_file)
    assert events[0]["format"] == "dotenv"


class TestFilterEvents:
    def _make_events(self):
        return [
            {"action": "set", "environment": "prod", "key": "DB"},
            {"action": "get", "environment": "prod", "key": "DB"},
            {"action": "set", "environment": "dev", "key": "TOKEN"},
            {"action": "rotate", "environment": "prod"},
        ]

    def test_filter_by_action(self):
        result = filter_events(self._make_events(), action="set")
        assert len(result) == 2
        assert all(e["action"] == "set" for e in result)

    def test_filter_by_environment(self):
        result = filter_events(self._make_events(), environment="dev")
        assert len(result) == 1
        assert result[0]["key"] == "TOKEN"

    def test_filter_by_key(self):
        result = filter_events(self._make_events(), key="DB")
        assert len(result) == 2

    def test_combined_filters(self):
        result = filter_events(self._make_events(), action="set", environment="prod")
        assert len(result) == 1
        assert result[0]["key"] == "DB"

    def test_no_match_returns_empty(self):
        result = filter_events(self._make_events(), action="delete")
        assert result == []
