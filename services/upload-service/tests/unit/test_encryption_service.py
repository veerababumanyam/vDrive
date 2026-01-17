"""Unit tests for encryption service."""

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.app.services.encryption_service import EncryptionService


@pytest.fixture
def encryption_service():
    """Create encryption service with test key."""
    service = EncryptionService()
    # Use a test master key (32 bytes = 64 hex chars)
    service.master_key = bytes.fromhex("0" * 64)
    return service


class TestKeyDerivation:
    """Test workspace key derivation."""

    def test_derive_workspace_key_returns_32_bytes(self, encryption_service):
        """Derived keys should be 32 bytes for AES-256."""
        key = encryption_service.derive_workspace_key("workspace-123")
        assert len(key) == 32

    def test_derive_workspace_key_is_deterministic(self, encryption_service):
        """Same workspace ID should produce same key."""
        key1 = encryption_service.derive_workspace_key("workspace-123")
        key2 = encryption_service.derive_workspace_key("workspace-123")
        assert key1 == key2

    def test_derive_workspace_key_differs_per_workspace(self, encryption_service):
        """Different workspace IDs should produce different keys."""
        key1 = encryption_service.derive_workspace_key("workspace-123")
        key2 = encryption_service.derive_workspace_key("workspace-456")
        assert key1 != key2

    def test_derive_workspace_key_differs_per_version(self, encryption_service):
        """Different key versions should produce different keys."""
        key1 = encryption_service.derive_workspace_key("workspace-123", version=1)
        key2 = encryption_service.derive_workspace_key("workspace-123", version=2)
        assert key1 != key2


class TestEncryption:
    """Test encryption and decryption."""

    def test_encrypt_decrypt_roundtrip(self, encryption_service):
        """Encrypted data should decrypt to original plaintext."""
        plaintext = b"Hello, World! This is test data."
        workspace_id = "workspace-123"

        # Generate encryption metadata
        metadata = encryption_service.generate_encryption_metadata()
        iv = bytes.fromhex(metadata["iv"])

        # Encrypt
        ciphertext, _, auth_tag = encryption_service.encrypt_chunk(
            plaintext,
            encryption_service.derive_workspace_key(workspace_id),
            iv,
        )

        # Decrypt
        decrypted = encryption_service.decrypt_data(
            ciphertext,
            encryption_service.derive_workspace_key(workspace_id),
            iv,
            auth_tag,
        )

        assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertext_with_different_iv(
        self, encryption_service
    ):
        """Same plaintext with different IVs should produce different ciphertext."""
        plaintext = b"Same plaintext"
        workspace_id = "workspace-123"
        key = encryption_service.derive_workspace_key(workspace_id)

        # Encrypt with first IV
        metadata1 = encryption_service.generate_encryption_metadata()
        iv1 = bytes.fromhex(metadata1["iv"])
        ciphertext1, _, _ = encryption_service.encrypt_chunk(plaintext, key, iv1)

        # Encrypt with second IV
        metadata2 = encryption_service.generate_encryption_metadata()
        iv2 = bytes.fromhex(metadata2["iv"])
        ciphertext2, _, _ = encryption_service.encrypt_chunk(plaintext, key, iv2)

        assert ciphertext1 != ciphertext2

    def test_decrypt_with_wrong_key_raises_error(self, encryption_service):
        """Decryption with wrong key should fail."""
        plaintext = b"Secret data"
        workspace_id = "workspace-123"
        wrong_workspace_id = "workspace-456"

        # Encrypt with workspace-123 key
        metadata = encryption_service.generate_encryption_metadata()
        iv = bytes.fromhex(metadata["iv"])
        key = encryption_service.derive_workspace_key(workspace_id)
        ciphertext, _, auth_tag = encryption_service.encrypt_chunk(plaintext, key, iv)

        # Try to decrypt with workspace-456 key
        wrong_key = encryption_service.derive_workspace_key(wrong_workspace_id)

        with pytest.raises(Exception):
            encryption_service.decrypt_data(ciphertext, wrong_key, iv, auth_tag)

    def test_decrypt_with_wrong_auth_tag_raises_error(self, encryption_service):
        """Decryption with wrong auth tag should fail."""
        plaintext = b"Secret data"
        workspace_id = "workspace-123"

        metadata = encryption_service.generate_encryption_metadata()
        iv = bytes.fromhex(metadata["iv"])
        key = encryption_service.derive_workspace_key(workspace_id)
        ciphertext, _, auth_tag = encryption_service.encrypt_chunk(plaintext, key, iv)

        # Tamper with auth tag
        tampered_auth_tag = bytes([b ^ 0xFF for b in auth_tag])

        with pytest.raises(Exception):
            encryption_service.decrypt_data(ciphertext, key, iv, tampered_auth_tag)


class TestChunkEncryption:
    """Test streaming chunk encryption."""

    def test_encrypt_multiple_chunks_with_same_iv(self, encryption_service):
        """Multiple chunks can be encrypted with the same IV but different offsets."""
        workspace_id = "workspace-123"
        key = encryption_service.derive_workspace_key(workspace_id)
        metadata = encryption_service.generate_encryption_metadata()
        iv = bytes.fromhex(metadata["iv"])

        chunks = [b"Chunk 1 data", b"Chunk 2 data", b"Chunk 3 data"]
        encrypted_chunks = []

        for chunk in chunks:
            ciphertext, offset, auth_tag = encryption_service.encrypt_chunk(chunk, key, iv)
            encrypted_chunks.append((ciphertext, auth_tag))

        # Each chunk should have different ciphertext
        assert encrypted_chunks[0][0] != encrypted_chunks[1][0]
        assert encrypted_chunks[1][0] != encrypted_chunks[2][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
