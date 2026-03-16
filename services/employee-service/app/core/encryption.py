"""AES-256-GCM transparent column encryption for PII fields."""
import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import TypeDecorator, String


class EncryptedString(TypeDecorator):
    """SQLAlchemy TypeDecorator that transparently encrypts/decrypts string columns.

    Storage format: base64(12-byte-nonce || ciphertext+16-byte-tag)
    Key source: settings.PII_ENCRYPTION_KEY (64 hex chars = 32-byte AES-256 key)
    """

    impl = String
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.core.config import settings
        raw = bytes.fromhex(settings.PII_ENCRYPTION_KEY)
        self._aes = AESGCM(raw)

    def process_bind_param(self, value, dialect):
        """Encrypt on write."""
        if value is None:
            return None
        nonce = os.urandom(12)
        ct = self._aes.encrypt(nonce, value.encode("utf-8"), None)
        return base64.b64encode(nonce + ct).decode("ascii")

    def process_result_value(self, value, dialect):
        """Decrypt on read."""
        if value is None:
            return None
        raw = base64.b64decode(value.encode("ascii"))
        nonce, ct = raw[:12], raw[12:]
        return self._aes.decrypt(nonce, ct, None).decode("utf-8")
