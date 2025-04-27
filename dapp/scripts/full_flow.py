"""
Interactive demo: Local Ethereum vault + Pinata IPFS storage.

Requirements
------------
* `ape test` provider (Hardhat) – launched automatically by `ape run`
* .env must contain PINATA_API_KEY and PINATA_API_SECRET
* Optional FERNET_KEY (32-byte url-safe base64). If absent it’s generated
  once and persisted to .env for future runs.
"""

import os, sys, time, getpass, json, textwrap
from pathlib import Path
from dotenv import load_dotenv, set_key

# ── Make sure `dapp/` is importable ────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Ape & helpers ──────────────────────────────────────────────
from ape import accounts, project, networks
from ipfs.pinata_client import pin_file, fetch_ipfs
from ipfs.encryption    import generate_key, encrypt_blob, decrypt_blob

BLOB_DIR = SCRIPT_DIR / "vault_blobs"
BLOB_DIR.mkdir(exist_ok=True)

# -----------------------------------------------------------------
def banner():
    print(textwrap.dedent("""\
        ╔══════════════════════════════════════════════════════════════╗
        ║  🏛  Decentralised Vault Demo                                ║
        ║  • Stores *encrypted* secrets on IPFS via Pinata             ║
        ║  • Stores only the CID+title on an Ethereum smart-contract   ║
        ║  • Your symmetric key never leaves your machine              ║
        ╚══════════════════════════════════════════════════════════════╝
    """))

# -----------------------------------------------------------------
def choose_account():
    print("Choose one of the built-in local test accounts:")
    for i, acct in enumerate(accounts.test_accounts):
        print(f"    [{i}] {acct.address}")
    idx = int(input("Pick index 0-19 → ").strip())
    return accounts.test_accounts[idx]

# -----------------------------------------------------------------
def ensure_key(dotenv_path):
    raw = os.getenv("FERNET_KEY")
    if raw:
        print("🔑 Using existing FERNET_KEY from .env")
        return raw.encode()

    key = generate_key()
    print("🔑 Generated new symmetric key:", key.decode())
    set_key(str(dotenv_path), "FERNET_KEY", key.decode())
    print("🔑 Saved FERNET_KEY into .env ✔")
    return key

# -----------------------------------------------------------------
def deploy_if_needed(owner):
    if "Vault" in project:
        # re-use existing artifact
        pass
    vault = owner.deploy(project.Vault)
    print("🏛  Vault deployed →", vault.address)
    return vault

# -----------------------------------------------------------------
def list_items(vault, owner, key):
    items = vault.getMyItems(sender=owner)
    if not items:
        print("📭 No vault items yet.")
        return

    while True:
        print(f"📦 You have {len(items)} item(s):")
        for idx, it in enumerate(items):
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(it.created))
            print(f"   [{idx}]  cid={it.cid}  title={it.title}  @ {ts}")

        choice = input("Decrypt one? index / <enter>=back → ").strip()
        if choice == "":
            # user chose to go back
            return

        if not choice.isdigit():
            print("❌ Please enter a number or just press Enter to go back.")
            continue

        i = int(choice)
        if i < 0 or i >= len(items):
            print(f"❌ No item at index {i}. Choose a valid index or press Enter to go back.")
            continue

        # valid index chosen
        cid = items[i].cid
        print("⏳ Fetching from IPFS …")
        data = fetch_ipfs(cid)
        plain = decrypt_blob(key, data)
        print("🔓 Decrypted payload:", plain.decode())
        return


# -----------------------------------------------------------------
def create_item(vault, owner, key):
    title  = input("Title for this secret → ").strip()
    secret = getpass.getpass("Enter secret text → ").encode()

    ciphertext = encrypt_blob(key, secret)
    fname = BLOB_DIR / f"{int(time.time())}.enc"
    fname.write_bytes(ciphertext)
    print("✏️  Ciphertext saved →", fname)

    # Pin
    print("⏳ Pinning to Pinata …")
    cid = pin_file(str(fname))
    print("📌 Pinned! CID =", cid)

    # Store on-chain
    print("⛓  Sending createItem() …")
    receipt = vault.createItem(cid, title, sender=owner)
    print("✅ Tx mined @ block", receipt.block_number, "hash", receipt.txn_hash)

# -----------------------------------------------------------------
def delete_item(vault, owner):
    items = vault.getMyItems(sender=owner)
    if not items:
        print("📭 Nothing to delete.")
        return

    # Keep prompting until the user enters a valid index or cancels
    while True:
        print("Your items:")
        for idx, it in enumerate(items):
            print(f"   [{idx}]  {it.title}  {it.cid}")

        choice = input("Index to delete / <enter>=cancel → ").strip()
        if choice == "":
            # user chose to cancel
            return

        if not choice.isdigit():
            print("❌ Please enter a number or just press Enter to cancel.")
            continue

        i = int(choice)
        if i < 0 or i >= len(items):
            print(f"❌ No item at index {i}. Choose a valid index or press Enter to cancel.")
            continue

        # valid index chosen
        try:
            print(f"🗑  Deleting item [{i}] …")
            receipt = vault.deleteItem(i, sender=owner)
            print("✅ Deleted. Tx hash:", receipt.txn_hash)
        except Exception as e:
            print("⚠️  Delete failed:", e)
        return

# -----------------------------------------------------------------
def main():
    banner()

    # 0) env + key
    dotenv_path = PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=dotenv_path)
    key = ensure_key(dotenv_path)

    # 1) pick account
    owner = choose_account()
    print("👤 Active account:", owner.address)

    # 2) make sure provider is up (ape run already connected)
    print("🔌 Network:", networks.active_provider)

    # 3) deploy / load contract
    vault = deploy_if_needed(owner)

    # 4) REPL loop
    while True:
        print("\nMain menu — choose an action:")
        print("  1) List my vault items")
        print("  2) Create a new vault item")
        print("  3) Delete an item")
        print("  4) Quit")

        sel = input("→ ").strip()
        if sel == "1":
            list_items(vault, owner, key)
        elif sel == "2":
            create_item(vault, owner, key)
        elif sel == "3":
            delete_item(vault, owner)
        elif sel == "4":
            break
        else:
            print("Unknown choice — try again.")

    print("👋 Bye!")

# -----------------------------------------------------------------
if __name__ == "__main__":
    main()