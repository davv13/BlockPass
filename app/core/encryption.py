# app/core/encryption.py

from cryptography.fernet import Fernet, InvalidToken
from app.core.config import get_settings

settings = get_settings()
fernet = Fernet(settings.VAULT_KEY.encode())

def encrypt_data(plaintext: str) -> bytes:
    """
    Encrypt a UTF‑8 string and return the ciphertext bytes.
    """
    token = fernet.encrypt(plaintext.encode("utf-8"))
    return token

def decrypt_data(token: bytes) -> str:
    """
    Decrypt ciphertext bytes and return the original UTF‑8 string.
    Raises InvalidToken on tampering or wrong key.
    """
    try:
        data = fernet.decrypt(token)
        return data.decode("utf-8")
    except InvalidToken:
        raise