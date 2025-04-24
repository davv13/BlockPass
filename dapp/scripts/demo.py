# dapp/scripts/demo.py

import os
from ipfs.pinata_client import pin_file, fetch_ipfs
from ipfs.encryption import generate_key, encrypt_blob, decrypt_blob

def main():
    # 1) Your “secret” payload
    secret = b"My top-secret vault entry"

    # 2) Generate (or load) the user’s encryption key
    key = generate_key()
    print("🔑 Encryption key (save this!):", key.decode())

    # 3) Encrypt the payload
    ciphertext = encrypt_blob(key, secret)
    tmp = "secret.enc"
    with open(tmp, "wb") as f:
        f.write(ciphertext)

    # 4) Pin encrypted file → get back CID
    cid = pin_file(tmp)
    print("📌 Pinned to IPFS CID:", cid)

    # 5) Fetch & decrypt to verify
    data = fetch_ipfs(cid)
    plain = decrypt_blob(key, data)
    print("🔓 Decrypted payload:", plain.decode())

if __name__ == "__main__":
    main()