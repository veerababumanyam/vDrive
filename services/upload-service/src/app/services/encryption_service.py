"""AES-256-GCM encryption service with HKDF key derivation."""

import os
from typing import BinaryIO, Optional

import structlog
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from ..core.config import settings

logger = structlog.get_logger()

CHUNK_SIZE = 8192  # 8KB chunks for streaming


class EncryptionService:
    """AES-256-GCM encryption with HKDF key derivation."""

    def __init__(self):
        # Master key from environment (hex-encoded)
        self.master_key = bytes.fromhex(settings.ENCRYPTION_MASTER_KEY)
        if len(self.master_key) != 32:
            raise ValueError("ENCRYPTION_MASTER_KEY must be 32 bytes (64 hex chars)")

    def derive_workspace_key(self, workspace_id: str, version: int = 1) -> bytes:
        """Derive workspace-specific encryption key using HKDF-SHA256."""
        info = f"{workspace_id}:v{version}".encode()
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=info,
        )
        return hkdf.derive(self.master_key)

    def encrypt_data(self, data: bytes, key: bytes) -> tuple[bytes, bytes, bytes]:
        """Encrypt data with AES-256-GCM."""
        iv = os.urandom(12)  # 96-bit IV
        aesgcm = AESGCM(key)
        ciphertext_with_tag = aesgcm.encrypt(iv, data, None)
        # Split ciphertext and auth tag (last 16 bytes)
        ciphertext = ciphertext_with_tag[:-16]
        auth_tag = ciphertext_with_tag[-16:]
        return ciphertext, iv, auth_tag

    def decrypt_data(
        self, ciphertext: bytes, key: bytes, iv: bytes, auth_tag: bytes
    ) -> bytes:
        """Decrypt data with AES-256-GCM."""
        aesgcm = AESGCM(key)
        # Combine ciphertext and auth tag
        ciphertext_with_tag = ciphertext + auth_tag
        return aesgcm.decrypt(iv, ciphertext_with_tag, None)

    def encrypt_stream(
        self, input_stream: BinaryIO, key: bytes
    ) -> tuple[bytes, bytes, bytes]:
        """
        Encrypt stream with AES-256-GCM.
        Reads all data then encrypts as single blob for integrity.
        Returns: (encrypted_data, iv, auth_tag)
        """
        # Read all chunks
        chunks = []
        while True:
            chunk = input_stream.read(CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)

        # Encrypt entire data as single blob
        full_data = b"".join(chunks)
        return self.encrypt_data(full_data, key)

    def encrypt_chunk(
        self, chunk: bytes, key: bytes, iv: Optional[bytes] = None
    ) -> tuple[bytes, bytes, bytes]:
        """Encrypt a single chunk (for multipart uploads)."""
        if iv is None:
            iv = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext_with_tag = aesgcm.encrypt(iv, chunk, None)
        ciphertext = ciphertext_with_tag[:-16]
        auth_tag = ciphertext_with_tag[-16:]
        return ciphertext, iv, auth_tag

    def generate_encryption_metadata(self) -> dict:
        """Generate IV and metadata for a new encryption operation."""
        iv = os.urandom(12)
        return {
            "iv": iv.hex(),
            "algorithm": "AES-256-GCM",
            "key_size": 256,
        }


# Singleton instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
