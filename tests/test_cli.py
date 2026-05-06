"""Tests for the envault CLI layer."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from envault.cli import build_parser, cmd_set, cmd_get, cmd_list


VAULT_PASSWORD = "test-password-123"


class TestCLISet(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.vault_path = os.path.join(self.tmpdir, "test.vault.json")

    def _make_args(self, **kwargs):
        class Args:
            pass
        a = Args()
        for k, v in kwargs.items():
            setattr(a, k, v)
        return a

    @patch("envault.cli.getpass.getpass", return_value=VAULT_PASSWORD)
    def test_set_creates_vault(self, _mock):
        args = self._make_args(vault=self.vault_path, env="staging", pairs=["DB_URL=postgres://localhost/db"])
        cmd_set(args)
        self.assertTrue(os.path.exists(self.vault_path))

    @patch("envault.cli.getpass.getpass", return_value=VAULT_PASSWORD)
    def test_set_and_get_roundtrip(self, _mock):
        set_args = self._make_args(vault=self.vault_path, env="production", pairs=["API_KEY=secret123", "DEBUG=false"])
        cmd_set(set_args)

        get_args = self._make_args(vault=self.vault_path, env="production", key=None)
        import io
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            cmd_get(get_args)
            output = mock_out.getvalue()
        self.assertIn("API_KEY=secret123", output)
        self.assertIn("DEBUG=false", output)

    @patch("envault.cli.getpass.getpass", return_value=VAULT_PASSWORD)
    def test_get_single_key(self, _mock):
        set_args = self._make_args(vault=self.vault_path, env="dev", pairs=["TOKEN=abc"])
        cmd_set(set_args)

        get_args = self._make_args(vault=self.vault_path, env="dev", key="TOKEN")
        import io
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            cmd_get(get_args)
            output = mock_out.getvalue().strip()
        self.assertEqual(output, "abc")

    @patch("envault.cli.getpass.getpass", return_value=VAULT_PASSWORD)
    def test_get_missing_key_exits(self, _mock):
        set_args = self._make_args(vault=self.vault_path, env="dev", pairs=["TOKEN=abc"])
        cmd_set(set_args)

        get_args = self._make_args(vault=self.vault_path, env="dev", key="NONEXISTENT")
        with self.assertRaises(SystemExit):
            cmd_get(get_args)

    @patch("envault.cli.getpass.getpass", return_value=VAULT_PASSWORD)
    def test_list_environments(self, _mock):
        for env in ("alpha", "beta", "gamma"):
            args = self._make_args(vault=self.vault_path, env=env, pairs=["X=1"])
            cmd_set(args)

        list_args = self._make_args(vault=self.vault_path)
        import io
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            cmd_list(list_args)
            output = mock_out.getvalue()
        for env in ("alpha", "beta", "gamma"):
            self.assertIn(env, output)


class TestCLIParser(unittest.TestCase):
    def test_set_command_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["set", "production", "KEY=val"])
        self.assertEqual(args.command, "set")
        self.assertEqual(args.env, "production")
        self.assertEqual(args.pairs, ["KEY=val"])

    def test_get_command_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["get", "staging", "MY_KEY"])
        self.assertEqual(args.command, "get")
        self.assertEqual(args.key, "MY_KEY")

    def test_list_command_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["list"])
        self.assertEqual(args.command, "list")


if __name__ == "__main__":
    unittest.main()
