# #!/usr/bin/env python3
# # dapp/scripts/full_flow.py

# """
# End-to-end demo:

#   1. load your ENV (Pinata & optional FERNET_KEY)
#   2. rely on `ape run` to start the built-in test chain
#   3. deploy Vault.sol
#   4. encrypt → pin to Pinata → get CID
#   5. store CID on‐chain via createItem()
#   6. read back, fetch from IPFS, decrypt
# """

# import os, sys
# from dotenv import load_dotenv

# # ── make sure “dapp/” root is on our import path ─────────────────
# SCRIPT_DIR   = os.path.dirname(__file__)
# PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
# sys.path.insert(0, PROJECT_ROOT)

# # ── Ape SDK & our IPFS helpers ───────────────────────────────────
# from ape import accounts, project, networks
# from ipfs.pinata_client  import pin_file, fetch_ipfs
# from ipfs.encryption      import generate_key, encrypt_blob, decrypt_blob

# def main():
#     # 1) Load your .env
#     load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

#     # 2) (ape run will have already connected us to the “test” chain)
#     print("▶ active provider:", networks.active_provider)

#     # pick the first test account
#     owner = accounts.test_accounts[0]
#     print("👤 Using account:", owner.address)

#     # 3) Deploy Vault.sol
#     vault = owner.deploy(project.Vault)
#     print("🏛  Deployed Vault at:", vault.address)

#     # 4) Get or generate your Fernet key
#     raw_key = os.getenv("FERNET_KEY")
#     if raw_key:
#         key = raw_key.encode()
#         print("🔑 Loaded key from .env")
#     else:
#         key = generate_key()
#         print("🔑 Generated new key:", key.decode())
#         print("   (Tip: add FERNET_KEY=", key.decode(), "to your .env to reuse)")

#     # 5) Your secret payload
#     secret = b"mysecretpass"
#     print("🔐 Secret payload:", secret.decode())

#     # 6) Encrypt → write to a temp file
#     ciphertext = encrypt_blob(key, secret)
#     tmp_file   = os.path.join(SCRIPT_DIR, "secret.enc")
#     with open(tmp_file, "wb") as f:
#         f.write(ciphertext)
#     print("✏️  Encrypted payload written to", tmp_file)

#     # 7) Pin to Pinata → CID
#     cid = pin_file(tmp_file)
#     print("📌 Pinned to IPFS (Pinata) → CID:", cid)

#     # 8) Store that CID on‐chain
#     tx_hash = vault.createItem(cid, "EmailPassword", sender=owner)
#     print("✅ createItem tx hash:", tx_hash)

#     # 9) Read back your on‐chain items
#     items = vault.getMyItems(sender=owner)
#     print(f"📦 You have {len(items)} item(s) in your Vault:")
#     for idx, it in enumerate(items):
#         print(f"   • [{idx}] cid={it.cid}  title={it.title}")

#     # 10) Fetch & decrypt
#     data  = fetch_ipfs(cid)
#     plain = decrypt_blob(key, data)
#     print("🔓 Decrypted payload:", plain.decode())


# if __name__ == "__main__":
#     main()



#!/usr/bin/env python3
# dapp/scripts/full_flow.py

"""
End-to-end demo:

  1. load your ENV (Pinata & optional FERNET_KEY)
  2. rely on `ape run` to start the built-in test chain
  3. deploy Vault.sol
  4. encrypt → pin to Pinata → get CID
  5. store CID on‐chain via createItem()
  6. read back, fetch from IPFS, decrypt
"""

import os
import sys
from dotenv import load_dotenv

# ── make sure “dapp/” root is on our import path ─────────────────
SCRIPT_DIR   = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

# ── Ape SDK & our IPFS helpers ───────────────────────────────────
from ape import accounts, project, networks
from ipfs.pinata_client  import pin_file, fetch_ipfs
from ipfs.encryption      import generate_key, encrypt_blob, decrypt_blob

def main():
    # 1) Load your .env
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    # 2) (ape run will have already connected us to the “test” chain)
    print("▶ active provider:", networks.active_provider)

    # pick the first test account
    owner = accounts.test_accounts[0]
    print("👤 Using account:", owner.address)

    # 3) Deploy Vault.sol
    vault = owner.deploy(project.Vault)
    print("🏛  Deployed Vault at:", vault.address)

    # 4) Get or generate your Fernet key
    raw_key = os.getenv("FERNET_KEY")
    if raw_key:
        key = raw_key.encode()
        print("🔑 Loaded key from .env")
    else:
        key = generate_key()
        print("🔑 Generated new key:", key.decode())
        print("   (Tip: add FERNET_KEY=", key.decode(), "to your .env to reuse)")

    # 5) Your secret payload
    secret = b"mysecretpass"
    print("🔐 Secret payload:", secret.decode())

    # 6) Encrypt → write to a temp file
    ciphertext = encrypt_blob(key, secret)
    tmp_file   = os.path.join(SCRIPT_DIR, "secret.enc")
    with open(tmp_file, "wb") as f:
        f.write(ciphertext)
    print("✏️  Encrypted payload written to", tmp_file)

    # 7) Pin to Pinata → CID
    cid = pin_file(tmp_file)
    print("📌 Pinned to IPFS (Pinata) → CID:", cid)

    # 8) Store that CID on‐chain
    receipt = vault.createItem(cid, "EmailPassword", sender=owner)
    # <— no more .hex(), txn_hash is already a string
    print("✅ createItem tx hash:", receipt.txn_hash)

    # 9) Read back your on‐chain items
    items = vault.getMyItems(sender=owner)
    print(f"📦 You have {len(items)} item(s) in your Vault:")
    for idx, it in enumerate(items):
        print(f"   • [{idx}] cid={it.cid}  title={it.title}")

    # 10) Fetch & decrypt
    data  = fetch_ipfs(cid)
    plain = decrypt_blob(key, data)
    print("🔓 Decrypted payload:", plain.decode())

if __name__ == "__main__":
    main()
