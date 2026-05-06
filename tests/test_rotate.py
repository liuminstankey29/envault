"""Tests for envault.rotate secret-rotation helpers."""

from __future__ import annotations

import os
import tempfile
import pytest

from envault.vault import write_secrets, read_secrets, list_environments
from envault.rotate import rotate_environment, rotate_all_environments


@pytest.fixture()
def vault_file():
    with tempfile.NamedTemporaryFile(suffix=".vault", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


OLD_PWD = "old-password-123"
NEW_PWD = "new-password-456"


class TestRotateEnvironment:
    def test_secrets_readable_with_new_password(self, vault_file):
        write_secrets(vault_file, "prod", {"KEY": "value"}, OLD_PWD)
        rotate_environment(vault_file, "prod", OLD_PWD, NEW_PWD)
        secrets = read_secrets(vault_file, "prod", NEW_PWD)
        assert secrets == {"KEY": "value"}

    def test_old_password_rejected_after_rotation(self, vault_file):
        write_secrets(vault_file, "prod", {"KEY": "value"}, OLD_PWD)
        rotate_environment(vault_file, "prod", OLD_PWD, NEW_PWD)
        with pytest.raises(Exception):
            read_secrets(vault_file, "prod", OLD_PWD)

    def test_returns_count_of_rotated_secrets(self, vault_file):
        write_secrets(vault_file, "staging", {"A": "1", "B": "2"}, OLD_PWD)
        count = rotate_environment(vault_file, "staging", OLD_PWD, NEW_PWD)
        assert count == 2

    def test_empty_environment_returns_zero(self, vault_file):
        # environment does not exist yet
        count = rotate_environment(vault_file, "ghost", OLD_PWD, NEW_PWD)
        assert count == 0


class TestRotateAllEnvironments:
    def test_all_envs_rotated(self, vault_file):
        write_secrets(vault_file, "dev", {"X": "1"}, OLD_PWD)
        write_secrets(vault_file, "prod", {"Y": "2", "Z": "3"}, OLD_PWD)
        envs = list_environments(vault_file)
        results = rotate_all_environments(vault_file, OLD_PWD, NEW_PWD, envs)
        assert results["dev"] == 1
        assert results["prod"] == 2

    def test_data_intact_after_bulk_rotate(self, vault_file):
        write_secrets(vault_file, "dev", {"TOKEN": "abc"}, OLD_PWD)
        write_secrets(vault_file, "prod", {"TOKEN": "xyz"}, OLD_PWD)
        envs = list_environments(vault_file)
        rotate_all_environments(vault_file, OLD_PWD, NEW_PWD, envs)
        assert read_secrets(vault_file, "dev", NEW_PWD) == {"TOKEN": "abc"}
        assert read_secrets(vault_file, "prod", NEW_PWD) == {"TOKEN": "xyz"}
