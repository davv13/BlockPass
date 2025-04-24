# dapp/ipfs/pinata_client.py

import os
import requests
from dotenv import load_dotenv

# Load PINATA_API_KEY & PINATA_API_SECRET from dapp/.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

PINATA_BASE = "https://api.pinata.cloud"
API_KEY    = os.environ["PINATA_API_KEY"]
API_SECRET = os.environ["PINATA_API_SECRET"]

HEADERS = {
    "pinata_api_key": API_KEY,
    "pinata_secret_api_key": API_SECRET,
}

def pin_json(obj: dict) -> str:
    """Pin a JSON object to IPFS via Pinata → returns CID."""
    url = f"{PINATA_BASE}/pinning/pinJSONToIPFS"
    r = requests.post(url, json=obj, headers=HEADERS)
    r.raise_for_status()
    return r.json()["IpfsHash"]

def pin_file(filepath: str) -> str:
    """Pin a local file to IPFS via Pinata → returns CID."""
    url = f"{PINATA_BASE}/pinning/pinFileToIPFS"
    with open(filepath, "rb") as fp:
        files = {"file": fp}
        r = requests.post(url, files=files, headers=HEADERS)
    r.raise_for_status()
    return r.json()["IpfsHash"]

def fetch_ipfs(cid: str) -> bytes:
    """Fetch raw bytes from the public Pinata gateway by CID."""
    gateway = f"https://gateway.pinata.cloud/ipfs/{cid}"
    r = requests.get(gateway)
    r.raise_for_status()
    return r.content
