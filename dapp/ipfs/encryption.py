# dapp/ipfs/encryption.py

import secrets, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def generate_key() -> bytes:
    """
    Generate a new 256-bit key, Base64-encode it for storage in .env.
    """
    raw_key = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(raw_key)

def encrypt_blob(key: bytes, data: bytes) -> bytes:
    """
    Encrypt plaintext → ciphertext. We pack nonce||ciphertext||tag together.
    """
    # key comes in Base64 form, so decode it:
    raw_key = base64.urlsafe_b64decode(key)
    aesgcm  = AESGCM(raw_key)
    nonce   = secrets.token_bytes(12)            # 96-bit nonce for GCM
    ct      = aesgcm.encrypt(nonce, data, None)  # no AAD here
    return nonce + ct

def decrypt_blob(key: bytes, blob: bytes) -> bytes:
    """
    Decrypt nonce||ciphertext||tag → original plaintext.
    """
    raw_key = base64.urlsafe_b64decode(key)
    aesgcm  = AESGCM(raw_key)
    nonce, ct = blob[:12], blob[12:]
    return aesgcm.decrypt(nonce, ct, None)
