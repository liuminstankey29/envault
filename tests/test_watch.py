"""Tests for envault.watch and envault.cli_watch."""

from __future__ import annotations

import io
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.vault import write_secrets
from envault.watch import _secrets_hash, watch_environment


@pytest.fixture()
def vault_file(tmp_path: Path) -> str:
    p = str(tmp_path / "vault.env")
    write_secrets(p, "prod", "pass1", {"KEY": "value1"})
    return p


def test_secrets_hash_is_stable(vault_file: str) -> None:
    h1 = _secrets_hash(vault_file, "prod", "pass1")
    h2 = _secrets_hash(vault_file, "prod", "pass1")
    assert h1 == h2


def test_secrets_hash_changes_after_write(vault_file: str) -> None:
    h1 = _secrets_hash(vault_file, "prod", "pass1")
    write_secrets(vault_file, "prod", "pass1", {"KEY": "value1", "NEW": "extra"})
    h2 = _secrets_hash(vault_file, "prod", "pass1")
    assert h1 != h2


def test_secrets_hash_bad_password_returns_empty_hash(vault_file: str) -> None:
    h = _secrets_hash(vault_file, "prod", "wrongpass")
    # Should not raise; returns hash of empty dict
    assert isinstance(h, str) and len(h) == 64


def test_watch_calls_on_change_when_secrets_change(vault_file: str) -> None:
    calls: list[tuple[dict, dict]] = []

    def _change(old: dict, new: dict) -> None:
        calls.append((old, new))

    # Patch time.sleep to avoid real waiting and inject a write on the first poll
    original_sleep = __import__("time").sleep
    poll_count = 0

    def fake_sleep(n: float) -> None:
        nonlocal poll_count
        poll_count += 1
        if poll_count == 1:
            write_secrets(vault_file, "prod", "pass1", {"KEY": "changed"})

    with patch("envault.watch.time.sleep", side_effect=fake_sleep):
        watch_environment(
            vault_file,
            "prod",
            "pass1",
            interval=0.01,
            on_change=_change,
            max_iterations=2,
        )

    assert len(calls) == 1
    old, new = calls[0]
    assert old == {"KEY": "value1"}
    assert new == {"KEY": "changed"}


def test_watch_no_change_does_not_call_on_change(vault_file: str) -> None:
    calls: list = []

    with patch("envault.watch.time.sleep"):
        watch_environment(
            vault_file,
            "prod",
            "pass1",
            interval=0.01,
            on_change=lambda o, n: calls.append((o, n)),
            max_iterations=3,
        )

    assert calls == []


def test_watch_runs_shell_command_on_change(vault_file: str) -> None:
    poll_count = 0

    def fake_sleep(n: float) -> None:
        nonlocal poll_count
        poll_count += 1
        if poll_count == 1:
            write_secrets(vault_file, "prod", "pass1", {"KEY": "v2"})

    with patch("envault.watch.time.sleep", side_effect=fake_sleep), \
         patch("envault.watch.subprocess.run") as mock_run:
        watch_environment(
            vault_file,
            "prod",
            "pass1",
            interval=0.01,
            shell_command="echo changed",
            max_iterations=2,
        )

    mock_run.assert_called_once_with("echo changed", shell=True, check=False)
