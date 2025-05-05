from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets
import base64
import json

def encrypt(plaintext: str, key: bytes) -> str:
    aesgcm = AESGCM(key)
    nonce  = secrets.token_bytes(12)          # 96‑bit
    ct     = aesgcm.encrypt(nonce, plaintext.encode(), None)
    # split tag and ciphertext (tag = last 16 bytes)
    tag, cipher = ct[-16:], ct[:-16]
    blob = {
        "nonce":     base64.b64encode(nonce).decode(),
        "ciphertext":base64.b64encode(cipher).decode(),
        "tag":       base64.b64encode(tag).decode(),
    }
    return json.dumps(blob)

def decrypt(blob_json: str, key: bytes) -> str:
    blob = json.loads(blob_json)
    nonce  = base64.b64decode(blob["nonce"])
    cipher = base64.b64decode(blob["ciphertext"])
    tag    = base64.b64decode(blob["tag"])
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, cipher + tag, None)
    return plaintext.decode()
