"""
Interactive demo: Decentralised Vault
• Encrypts secrets locally (Fernet)
• Pins ciphertext to IPFS via Pinata
• Stores only CID + title on Ethereum

Requirements
------------
* .env must contain PINATA_API_KEY and PINATA_API_SECRET
* Optional: PRIVATE_KEY and SEPOLIA_RPC_URL for Sepolia/Infura runs
* Optional: FERNET_KEY (generated & saved automatically if absent)
"""

import os, sys, time, getpass, textwrap
from pathlib import Path
from dotenv import load_dotenv, set_key

# --- helpers ---------------------------------------------------------------
from pathlib import Path
import json, os
from eth_account import Account
from ape import accounts

KEY_ALIAS = "deployer"
KEYSTORE_DIR = Path.home() / ".ape" / "accounts"
KEYSTORE_DIR.mkdir(parents=True, exist_ok=True)
KEYSTORE_FILE = KEYSTORE_DIR / f"{KEY_ALIAS}.json"

# ── Import project root ─────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Ape & helpers ───────────────────────────────────────────────
from ape import accounts, project, networks
from ipfs.pinata_client import pin_file, fetch_ipfs
from ipfs.encryption    import generate_key, encrypt_blob, decrypt_blob

BLOB_DIR = SCRIPT_DIR / "vault_blobs"
BLOB_DIR.mkdir(exist_ok=True)

def ensure_keystore_from_env():
    """
    If the 'deployer' alias doesn't exist but PRIVATE_KEY is in the env,
    create an un-encrypted keystore file so Ape will pick it up automatically
    next time (and immediately in this process via accounts.load()).
    """
    if KEY_ALIAS in list(accounts.aliases):
        return  # already available

    raw_pk = os.getenv("PRIVATE_KEY", "").removeprefix("0x")
    if not raw_pk:
        return  # nothing we can do

    # Create a keystore with **blank pass-phrase** so it's non-interactive.
    ks = Account.encrypt(raw_pk, "")          # ""  ==> no password prompt
    with KEYSTORE_FILE.open("w") as fh:
        json.dump(ks, fh)

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
    try:
        acct = accounts.load("deployer")      # comes from YAML
        print(f"🔑 Using config-file account: {acct.address}")
        return acct
    except KeyError:
        # fallback only for a local Hardhat/Fork run
        if networks.active_provider.name == "test":
            return accounts.test_accounts[0]
        raise RuntimeError(
            "Alias 'deployer' not found – check ape-config.yaml location/indent"
        )

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
    vault = owner.deploy(project.Vault)
    print("🏛  Vault deployed →", vault.address)
    return vault

# -----------------------------------------------------------------
def list_items(vault, owner, key):
    # Pull everything, then drop any items with no CID (e.g. deleted slots)
    items = [it for it in vault.getMyItems(sender=owner) if it.cid]
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
            return
        if not choice.isdigit() or not (0 <= int(choice) < len(items)):
            print("❌ Invalid choice.")
            continue

        cid = items[int(choice)].cid
        print("⏳ Fetching from IPFS …")
        data  = fetch_ipfs(cid)
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

    print("⏳ Pinning to Pinata …")
    cid = pin_file(str(fname))
    print("📌 Pinned! CID =", cid)

    print("⛓  Sending createItem() …")
    receipt = vault.createItem(cid, title, sender=owner)
    print("✅ Tx mined @ block", receipt.block_number, "hash", receipt.txn_hash)

# -----------------------------------------------------------------
def delete_item(vault, owner):
    items = vault.getMyItems(sender=owner)
    if not items:
        print("📭 Nothing to delete.")
        return

    while True:
        for idx, it in enumerate(items):
            print(f"   [{idx}]  {it.title}  {it.cid}")
        choice = input("Index to delete / <enter>=cancel → ").strip()
        if choice == "":
            return
        if not choice.isdigit() or not (0 <= int(choice) < len(items)):
            print("❌ Invalid choice.")
            continue
        try:
            print(f"🗑  Deleting item [{choice}] …")
            receipt = vault.deleteItem(int(choice), sender=owner)
            print("✅ Deleted. Tx hash:", receipt.txn_hash)
        except Exception as e:
            print("⚠️  Delete failed:", e)
        return

# -----------------------------------------------------------------
def main():
    ensure_keystore_from_env() 
    banner()

    # 0) env + key
    dotenv_path = PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=dotenv_path)
    key = ensure_key(dotenv_path)

    # 1) pick account (env-key or local test)
    owner = choose_account()
    print("👤 Active account:", owner.address)
    print("🔌 Network:", networks.active_provider)

    # 2) deploy / load contract
    vault = deploy_if_needed(owner)

    # 3) simple REPL
    while True:
        print("\nMain menu:")
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