"""Decryption service for processing encrypted assets."""

import structlog
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from ..core.config import settings

logger = structlog.get_logger()


class EncryptionService:
    """Decrypt assets encrypted with AES-256-GCM."""

    def __init__(self):
        """Initialize encryption service."""
        self.master_key = bytes.fromhex(settings.ENCRYPTION_MASTER_KEY)
        if len(self.master_key) != 32:
            raise ValueError("ENCRYPTION_MASTER_KEY must be 32 bytes (64 hex chars)")

    def derive_workspace_key(self, workspace_id: str, version: int = 1) -> bytes:
        """
        Derive workspace-specific encryption key using HKDF-SHA256.

        Args:
            workspace_id: Workspace ID
            version: Key version (default: 1)

        Returns:
            32-byte encryption key
        """
        info = f"{workspace_id}:v{version}".encode()
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=info,
        )
        return hkdf.derive(self.master_key)

    def decrypt_data(
        self, ciphertext: bytes, key: bytes, iv: bytes, auth_tag: bytes
    ) -> bytes:
        """
        Decrypt data with AES-256-GCM.

        Args:
            ciphertext: Encrypted data
            key: 32-byte encryption key
            iv: 12-byte initialization vector
            auth_tag: 16-byte authentication tag

        Returns:
            Decrypted plaintext
        """
        aesgcm = AESGCM(key)
        ciphertext_with_tag = ciphertext + auth_tag
        return aesgcm.decrypt(iv, ciphertext_with_tag, None)

    def decrypt_asset(
        self,
        encrypted_data: bytes,
        workspace_id: str,
        iv_hex: str,
        parts_metadata: list = None,
    ) -> bytes:
        """
        Decrypt asset downloaded from R2.

        Args:
            encrypted_data: Encrypted asset bytes
            workspace_id: Workspace ID for key derivation
            iv_hex: Hex-encoded IV
            parts_metadata: Optional parts metadata with auth tags

        Returns:
            Decrypted asset bytes
        """
        try:
            # Derive workspace key
            workspace_key = self.derive_workspace_key(workspace_id)

            # Decode IV
            iv = bytes.fromhex(iv_hex)

            # For multi-part uploads, validate auth tags exist but decrypt as single blob
            # Note: Per-part decryption would be implemented in production for streaming
            if parts_metadata and isinstance(parts_metadata, list):
                for part in parts_metadata:
                    if not part.get("AuthTag"):
                        logger.warning("Missing auth tag for part, attempting full decrypt")
                        break

            # Decrypt entire file
            # Note: For simplification, we're treating the entire encrypted file as one blob
            # The auth tag is embedded in the encryption process
            # In reality, multipart uploads would need per-part decryption

            aesgcm = AESGCM(workspace_key)

            # Try decrypting as a whole (this assumes encryption was done on full file)
            # Extract the last 16 bytes as auth tag
            if len(encrypted_data) < 16:
                raise ValueError("Encrypted data too short to contain auth tag")

            auth_tag = encrypted_data[-16:]
            ciphertext = encrypted_data[:-16]

            plaintext = aesgcm.decrypt(iv, ciphertext + auth_tag, None)

            logger.debug(
                "Asset decrypted",
                workspace_id=workspace_id,
                encrypted_size=len(encrypted_data),
                decrypted_size=len(plaintext),
            )

            return plaintext

        except Exception as e:
            logger.error(
                "Failed to decrypt asset",
                workspace_id=workspace_id,
                error=str(e),
            )
            raise


# Singleton instance
_encryption_service = None


def get_encryption_service() -> EncryptionService:
    """Get encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
