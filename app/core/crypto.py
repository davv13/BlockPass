from cryptography.fernet import Fernet
from app.core.config import get_settings

_settings = get_settings()
f = Fernet(_settings.VAULT_KEY.encode())

def encrypt(plaintext: str) -> bytes:
    return f.encrypt(plaintext.encode())

def decrypt(ciphertext: bytes) -> str:
    return f.decrypt(ciphertext).decode()