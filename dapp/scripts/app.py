# scripts/app.py
from pathlib import Path
import sys

# ── Make sure the `dapp/` folder (which contains ipfs/ and scripts/) is on the import path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import os, time, streamlit as st
from dotenv import load_dotenv
from web3 import Web3


import os, time, streamlit as st
from dotenv import load_dotenv
from pathlib import Path
from web3 import Web3
from eth_account import Account

# ── Load your .env ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
dotenv_path  = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=dotenv_path)

SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL")
PRIVATE_KEY     = os.getenv("PRIVATE_KEY")
raw_addr        = os.getenv("VAULT_ADDRESS")
# web3.py wants a checksum address:
if raw_addr is None:
    st.error("❌ VAULT_ADDRESS not set in .env"); st.stop()
VAULT_ADDRESS = Web3.to_checksum_address(raw_addr)
PINATA_API_KEY   = os.getenv("PINATA_API_KEY")
PINATA_API_SECRET= os.getenv("PINATA_API_SECRET")

if not all([SEPOLIA_RPC_URL, PRIVATE_KEY, VAULT_ADDRESS]):
    st.error("❌ SEPOLIA_RPC_URL, PRIVATE_KEY & VAULT_ADDRESS must be set in .env")
    st.stop()

# ── Web3 setup ───────────────────────────────────────────────────────────────
w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
if not w3.is_connected():
    st.error("⚠️  Could not connect to Sepolia RPC")
    st.stop()

acct = Account.from_key(PRIVATE_KEY)
st.success(f"🔑 Using account `{acct.address}` on Sepolia")

# ── Vault ABI (just the three methods we need) ───────────────────────────────
VAULT_ABI = [
    {
      "inputs":[
        {"internalType":"string","name":"cid","type":"string"},
        {"internalType":"string","name":"title","type":"string"}
      ],
      "name":"createItem","outputs":[],"stateMutability":"nonpayable","type":"function"
    },
    {
      "inputs":[],"name":"getMyItems",
      "outputs":[
        {"components":[
           {"internalType":"address","name":"owner","type":"address"},
           {"internalType":"string","name":"cid","type":"string"},
           {"internalType":"string","name":"title","type":"string"},
           {"internalType":"uint256","name":"created","type":"uint256"}
         ],
         "internalType":"struct Vault.Item[]","name":"","type":"tuple[]"
        }
      ],
      "stateMutability":"view","type":"function"
    },
    {
      "inputs":[{"internalType":"uint256","name":"itemId","type":"uint256"}],
      "name":"deleteItem","outputs":[],"stateMutability":"nonpayable","type":"function"
    },
]

vault = w3.eth.contract(address=VAULT_ADDRESS, abi=VAULT_ABI)

# ── Helpers from full_flow.py ────────────────────────────────────────────────
from ipfs.pinata_client import pin_file, fetch_ipfs
from ipfs.encryption    import generate_key, encrypt_blob, decrypt_blob
import json, requests, getpass
FERNET_KEY = os.getenv("FERNET_KEY").encode()

PINATA_BASE = "https://api.pinata.cloud"
HEADERS = {
    "pinata_api_key": PINATA_API_KEY,
    "pinata_secret_api_key": PINATA_API_SECRET,
}

def unpin_file(cid: str):
    url = f"{PINATA_BASE}/pinning/unpin/{cid}"
    r = requests.delete(url, headers=HEADERS)
    r.raise_for_status()


# ── Streamlit Layout ────────────────────────────────────────────────────────
st.title("🏛 Decentralised Vault")

st.header("🔒 My secrets")
if st.button("🔄 Refresh"):
    st.experimental_rerun()

# 1) fetch & display
items = vault.functions.getMyItems().call({"from": acct.address})
items = [it for it in items if it[1]]  # filter out deleted (cid == "")
if not items:
    st.info("No items yet.")
else:
    for idx, (owner, cid, title, created) in enumerate(items):
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created))
        with st.expander(f"{title}  ({ts})"):
            if st.button("🔓 Decrypt", key=f"dec{idx}"):
                data  = fetch_ipfs(cid)
                plain = decrypt_blob(FERNET_KEY, data)
                st.code(plain.decode())

            if st.button("🗑 Delete", key=f"del{idx}"):
                # on-chain delete
                nonce = w3.eth.get_transaction_count(acct.address)
                tx = vault.functions.deleteItem(idx).build_transaction({
                    "from": acct.address,
                    "nonce": nonce,
                    "maxFeePerGas": w3.to_wei(50, "gwei"),
                    "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
                })
                signed = acct.sign_transaction(tx)
                txh = w3.eth.send_raw_transaction(signed.rawTransaction)
                w3.eth.wait_for_transaction_receipt(txh)
                # unpin
                try:
                    unpin_file(cid)
                except Exception as e:
                    st.warning(f"Failed to unpin {cid}: {e}")
                st.success("Deleted on-chain & unpinned.")
                st.experimental_rerun()

st.header("➕ Add new secret")
with st.form("new"):
    title  = st.text_input("Title")
    secret = st.text_area("Secret text")
    ok = st.form_submit_button("Store")
    if ok:
        if not title or not secret:
            st.error("Both fields required")
        else:
            # encrypt + pin
            blob = encrypt_blob(FERNET_KEY, secret.encode())
            fname = PROJECT_ROOT / "scripts" / "vault.tmp.enc"
            fname.write_bytes(blob)
            cid   = pin_file(str(fname))
            # on-chain
            nonce = w3.eth.get_transaction_count(acct.address)
            tx = vault.functions.createItem(cid, title).build_transaction({
                "from": acct.address,
                "nonce": nonce,
                "maxFeePerGas": w3.to_wei(50, "gwei"),
                "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
            })
            signed = acct.sign_transaction(tx)
            txh = w3.eth.send_raw_transaction(signed.rawTransaction)
            w3.eth.wait_for_transaction_receipt(txh)

            st.success(f"Stored & pinned CID {cid}")
            st.experimental_rerun()