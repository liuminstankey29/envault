"""Tests for register_archive_parser argument definitions."""

from __future__ import annotations

import argparse
import pytest

from envault.cli_archive import register_archive_parser


@pytest.fixture
def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    register_archive_parser(sub)
    return root


def test_archive_basic_parses(parser):
    args = parser.parse_args(["archive", "vault.json", "prod", "mypass"])
    assert args.vault == "vault.json"
    assert args.environment == "prod"
    assert args.password == "mypass"
    assert args.output is None
    assert args.label is None


def test_archive_with_output_flag(parser):
    args = parser.parse_args(["archive", "v.json", "staging", "pw", "--output", "out.tar.gz"])
    assert args.output == "out.tar.gz"


def test_archive_with_label_flag(parser):
    args = parser.parse_args(["archive", "v.json", "prod", "pw", "--label", "weekly"])
    assert args.label == "weekly"


def test_restore_basic_parses(parser):
    args = parser.parse_args(["restore", "vault.json", "bundle.tar.gz", "mypass"])
    assert args.vault == "vault.json"
    assert args.archive == "bundle.tar.gz"
    assert args.password == "mypass"
    assert args.overwrite is False
    assert args.environment is None


def test_restore_overwrite_flag(parser):
    args = parser.parse_args(["restore", "v.json", "b.tar.gz", "pw", "--overwrite"])
    assert args.overwrite is True


def test_restore_environment_override(parser):
    args = parser.parse_args(["restore", "v.json", "b.tar.gz", "pw", "--environment", "canary"])
    assert args.environment == "canary"


def test_archive_has_func(parser):
    args = parser.parse_args(["archive", "v.json", "prod", "pw"])
    assert callable(args.func)


def test_restore_has_func(parser):
    args = parser.parse_args(["restore", "v.json", "b.tar.gz", "pw"])
    assert callable(args.func)
