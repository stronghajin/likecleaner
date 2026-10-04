"""Encryption for secrets kept at rest (refresh tokens, SPEC.md 3-2)."""

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _fernet() -> Fernet:
    key = get_settings().token_encryption_key.get_secret_value()
    if not key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is not set in backend/.env.")
    return Fernet(key)


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_secret(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()
