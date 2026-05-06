"""Tests for envault crypto and vault modules."""

import json
import pytest
from pathlib import Path
from envault.crypto import encrypt, decrypt
from envault.vault import write_secrets, read_secrets, list_environments


# ---------------------------------------------------------------------------
# Crypto tests
# ---------------------------------------------------------------------------

class TestEncryptDecrypt:
    PASSWORD = "super-secret-password"
    PLAINTEXT = "Hello, envault!"

    def test_encrypt_returns_string(self):
        result = encrypt(self.PLAINTEXT, self.PASSWORD)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_decrypt_roundtrip(self):
        token = encrypt(self.PLAINTEXT, self.PASSWORD)
        assert decrypt(token, self.PASSWORD) == self.PLAINTEXT

    def test_different_ciphertexts_same_plaintext(self):
        """Each encryption should produce a unique ciphertext (random nonce/salt)."""
        t1 = encrypt(self.PLAINTEXT, self.PASSWORD)
        t2 = encrypt(self.PLAINTEXT, self.PASSWORD)
        assert t1 != t2

    def test_wrong_password_raises(self):
        token = encrypt(self.PLAINTEXT, self.PASSWORD)
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(token, "wrong-password")

    def test_corrupted_data_raises(self):
        with pytest.raises(ValueError):
            decrypt("notvalidbase64!!!", self.PASSWORD)


# ---------------------------------------------------------------------------
# Vault tests
# ---------------------------------------------------------------------------

class TestVault:
    PASSWORD = "vault-pass"
    SECRETS = {"DB_URL": "postgres://localhost/db", "API_KEY": "abc123"}

    def test_write_and_read_secrets(self, tmp_path):
        vault = tmp_path / ".envault"
        write_secrets(self.SECRETS, self.PASSWORD, vault_path=vault)
        result = read_secrets(self.PASSWORD, vault_path=vault)
        assert result == self.SECRETS

    def test_multiple_environments(self, tmp_path):
        vault = tmp_path / ".envault"
        write_secrets({"KEY": "prod-val"}, self.PASSWORD, environment="production", vault_path=vault)
        write_secrets({"KEY": "dev-val"}, self.PASSWORD, environment="development", vault_path=vault)
        prod = read_secrets(self.PASSWORD, environment="production", vault_path=vault)
        dev = read_secrets(self.PASSWORD, environment="development", vault_path=vault)
        assert prod["KEY"] == "prod-val"
        assert dev["KEY"] == "dev-val"

    def test_list_environments(self, tmp_path):
        vault = tmp_path / ".envault"
        write_secrets({}, self.PASSWORD, environment="staging", vault_path=vault)
        write_secrets({}, self.PASSWORD, environment="production", vault_path=vault)
        envs = list_environments(vault_path=vault)
        assert envs == ["production", "staging"]

    def test_missing_environment_raises(self, tmp_path):
        vault = tmp_path / ".envault"
        with pytest.raises(KeyError, match="ghost"):
            read_secrets(self.PASSWORD, environment="ghost", vault_path=vault)

    def test_wrong_password_on_read_raises(self, tmp_path):
        vault = tmp_path / ".envault"
        write_secrets(self.SECRETS, self.PASSWORD, vault_path=vault)
        with pytest.raises(ValueError):
            read_secrets("bad-pass", vault_path=vault)
