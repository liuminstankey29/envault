"""Tests for the 'audit' CLI sub-command."""

import argparse
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest

from envault.audit import record_event
from envault.cli_audit import cmd_audit, register_audit_parser


class Args:
    """Simple namespace mimic for argparse results."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def log_file(tmp_path):
    path = str(tmp_path / "audit.jsonl")
    for action, env, key in [
        ("set", "prod", "DB_URL"),
        ("get", "prod", "DB_URL"),
        ("set", "dev", "TOKEN"),
    ]:
        record_event(action, env, key=key, log_path=path)
    return path


def test_cmd_audit_text_output(log_file, capsys):
    args = Args(log=log_file, action=None, env=None, key=None, format="text")
    cmd_audit(args)
    captured = capsys.readouterr()
    assert "set" in captured.out
    assert "prod" in captured.out


def test_cmd_audit_json_output(log_file, capsys):
    import json
    args = Args(log=log_file, action=None, env=None, key=None, format="json")
    cmd_audit(args)
    captured = capsys.readouterr()
    events = json.loads(captured.out)
    assert isinstance(events, list)
    assert len(events) == 3


def test_cmd_audit_filter_by_action(log_file, capsys):
    args = Args(log=log_file, action="get", env=None, key=None, format="text")
    cmd_audit(args)
    captured = capsys.readouterr()
    assert "get" in captured.out
    lines = [l for l in captured.out.splitlines() if l.strip()]
    assert len(lines) == 1


def test_cmd_audit_filter_by_env(log_file, capsys):
    args = Args(log=log_file, action=None, env="dev", key=None, format="text")
    cmd_audit(args)
    captured = capsys.readouterr()
    assert "dev" in captured.out
    assert "prod" not in captured.out


def test_cmd_audit_no_events_message(tmp_path, capsys):
    empty_log = str(tmp_path / "empty.jsonl")
    args = Args(log=empty_log, action=None, env=None, key=None, format="text")
    cmd_audit(args)
    captured = capsys.readouterr()
    assert "No audit events found" in captured.err


def test_register_audit_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_audit_parser(subparsers)
    parsed = parser.parse_args(["audit", "--env", "prod", "--format", "json"])
    assert parsed.env == "prod"
    assert parsed.format == "json"
    assert parsed.func is cmd_audit
