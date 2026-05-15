"""Tests for envault.cli_broadcast."""
from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.broadcast import add_hook
from envault.cli_broadcast import cmd_broadcast


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "vault.env")


def test_cmd_broadcast_add_new(vault_path, capsys):
    args = Args(vault=vault_path, broadcast_cmd="add", url="https://example.com", events=None)
    cmd_broadcast(args)
    out = capsys.readouterr().out
    assert "Added hook" in out
    assert "https://example.com" in out


def test_cmd_broadcast_add_update(vault_path, capsys):
    add_hook(vault_path, "https://example.com")
    args = Args(vault=vault_path, broadcast_cmd="add", url="https://example.com", events=["secret.changed"])
    cmd_broadcast(args)
    out = capsys.readouterr().out
    assert "Updated hook" in out


def test_cmd_broadcast_remove_existing(vault_path, capsys):
    add_hook(vault_path, "https://example.com")
    args = Args(vault=vault_path, broadcast_cmd="remove", url="https://example.com")
    cmd_broadcast(args)
    out = capsys.readouterr().out
    assert "Removed hook" in out


def test_cmd_broadcast_remove_missing_exits_1(vault_path):
    args = Args(vault=vault_path, broadcast_cmd="remove", url="https://missing.example.com")
    with pytest.raises(SystemExit) as exc:
        cmd_broadcast(args)
    assert exc.value.code == 1


def test_cmd_broadcast_list_empty(vault_path, capsys):
    args = Args(vault=vault_path, broadcast_cmd="list")
    cmd_broadcast(args)
    out = capsys.readouterr().out
    assert "No webhooks" in out


def test_cmd_broadcast_list_shows_hooks(vault_path, capsys):
    add_hook(vault_path, "https://example.com", events=["secret.changed"])
    args = Args(vault=vault_path, broadcast_cmd="list")
    cmd_broadcast(args)
    out = capsys.readouterr().out
    assert "https://example.com" in out
    assert "secret.changed" in out


def _mock_response(status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_cmd_broadcast_send_success(vault_path, capsys):
    add_hook(vault_path, "https://example.com")
    args = Args(
        vault=vault_path,
        broadcast_cmd="send",
        event="secret.changed",
        environment="production",
        note="",
    )
    with patch("urllib.request.urlopen", return_value=_mock_response(200)):
        cmd_broadcast(args)
    out = capsys.readouterr().out
    assert "1/1" in out


def test_cmd_broadcast_send_no_hooks(vault_path, capsys):
    args = Args(
        vault=vault_path,
        broadcast_cmd="send",
        event="secret.changed",
        environment="",
        note="",
    )
    cmd_broadcast(args)
    out = capsys.readouterr().out
    assert "No matching hooks" in out
