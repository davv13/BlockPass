# dapp/ipfs/encryption.py

from cryptography.fernet import Fernet

def generate_key() -> bytes:
    """
    Generate a new Fernet key.
    Store this per-user (e.g. in front-end localStorage or derive from wallet).
    """
    return Fernet.generate_key()

def encrypt_blob(key: bytes, data: bytes) -> bytes:
    """Encrypt bytes → ciphertext."""
    return Fernet(key).encrypt(data)

def decrypt_blob(key: bytes, token: bytes) -> bytes:
    """Decrypt ciphertext → original bytes."""
    return Fernet(key).decrypt(token)
