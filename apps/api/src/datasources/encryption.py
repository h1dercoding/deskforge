"""Fernet encryption for data source credentials.

Fernet uses AES-128-CBC with HMAC-SHA256 for authenticated encryption.
The key is derived from ENCRYPTION_KEY via SHA-256, producing a 32-byte
key (of which Fernet uses the first 16 bytes for AES-128).
"""
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from src.config import settings


def _derive_key() -> bytes:
    """Derive a Fernet key from the encryption key setting."""
    key = settings.ENCRYPTION_KEY.encode()
    derived = hashlib.sha256(key).digest()
    return base64.urlsafe_b64encode(derived)


_fernet = None


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_derive_key())
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt a string using Fernet (AES-128-CBC + HMAC-SHA256)."""
    f = get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted string."""
    f = get_fernet()
    try:
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        raise ValueError("Failed to decrypt: invalid key or corrupted data")


def encrypt_dict(data: dict) -> str:
    """Encrypt a dictionary as JSON."""
    import json
    return encrypt(json.dumps(data))


def decrypt_dict(ciphertext: str) -> dict:
    """Decrypt a JSON string back to a dictionary."""
    import json
    return json.loads(decrypt(ciphertext))
