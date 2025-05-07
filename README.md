## 🔐 BlockPass - Secure Password Manager


BlockPass is a hands-on exploration of modern “zero-knowledge” password management—first in a classic client-server model, then fully decentralized on IPFS and Ethereum. In **Centralized mode**, a FastAPI backend with PostgreSQL, per-user Argon2id KDF, and AES-256-GCM keeps secrets encrypted at rest, while short-lived JWT sessions safeguard access. In **Decentralized mode**, your secrets live only off-chain on IPFS (pinned via Pinata) and ownership records run through a Solidity smart contract on Sepolia.

Whether you need a self-hosted vault behind your own firewall or a peer-to-peer system with public auditability, BlockPass walks you through every cryptographic choice and deployment step—so you can see exactly how salt, nonce, tag and CID combine to give you total control over your data. Start with Docker-Compose for a quick local demo, then switch to the blockchain to experience trustless, censorship-resistant storage in action.

Ready to dive in? Follow the sections below to get your environment up and running, learn how to register and reveal secrets, and understand the security trade-offs at every layer.

---
**⚠️ Important: Separate Virtual Environments for Centralized & Decentralized Apps**
--- 
If you bundle **all** dependencies into a single `requirements.txt`, running:

```bash
pip install -r requirements.txt
```

will install **every** package—FastAPI, bcrypt, psycopg2, eth-ape, web3, IPFS clients, Brownie/Ape-Solidity, etc.—into one environment. This can lead to

* version conflicts
* unnecessary bloat

---

### 🔀 Pattern #1: Split Requirements

Create **two** files:

```
requirements.txt         # core/backend dependencies
dapp/requirements.txt    # decentralized-app dependencies
```

| File                    | Contains                                                            |
| ----------------------- | ------------------------------------------------------------------- |
| `requirements.txt`      | FastAPI, SQLAlchemy, bcrypt, psycopg2, python-dotenv…               |
| `dapp/requirements.txt` | eth-ape, web3.py, ipfs-client, brownie/ape-solidity, python-dotenv… |

#### Workflow

1. **Clone the repo**

   ```bash
   git clone https://github.com/davv13/BlockPass.git
   cd BlockPass
   ```
2. **Install Centralized Server**

   ```bash
   pip install -r requirements.txt
   ```
3. **Install Decentralized DApp**
   (in the same venv or a fresh one)

   ```bash
   pip install -r dapp/requirements.txt
   ```

> • If you only need the centralized server, stop after step 2.
> • To work on or run the DApp, complete step 3.

---

### ⚙️ Quick “All-in-One” Command

If you *do* want everything at once:

```bash
pip install -r requirements.txt \
    && pip install -r dapp/requirements.txt
```

This guarantees each environment only gets exactly what it needs—no surprises!


## 🚀 Getting started — Centralized Mode (Docker Compose, PostgreSQL)

### Why Centralized?

A tried-and-true architecture: your vault runs on a single backend you control.  All secrets are encrypted client-side with per-user Argon2id-derived keys and AES-256-GCM before they ever hit the server.  FastAPI (with both REST and server-rendered views) sits in front of a PostgreSQL database, and short-lived JWTs in HttpOnly cookies keep sessions stateless and safe.  You get full governance over backups, scaling, and compliance—while still never exposing plaintext or master-keys on the server.


### Prerequisites

| Tool                        | Why you need it                               | Link                                                                     |
| --------------------------- | --------------------------------------------- | ------------------------------------------------------------------------ |
| **Git**                     | clone this repo                               | [https://git‑scm.com/downloads](https://git-scm.com/downloads)           |
| **Docker Engine + Compose** | run FastAPI, Postgres & pgAdmin in containers | [https://docs.docker.com/get-docker](https://docs.docker.com/get-docker) |

---

### 1 . Clone the repo

```bash
git clone https://github.com/davv13/BlockPass.git
cd BlockPass
```

---

### 2 . Create your `.env`
`.env` is **git‑ignored**; each developer keeps secrets locally.

```dotenv
################  Database  ################
DB_BACKEND=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres        # change in prod
POSTGRES_DB=blockpass
POSTGRES_HOST=db                  # ← docker‑compose service name
POSTGRES_PORT=5432

################  JWT  ################
JWT_SECRET=supersecretkey123      # change in prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

*(Notice: **no `VAULT_KEY`** — vault keys are derived per‑user with Argon2id.)*

---

### 3 . Build & run

```bash
docker compose up --build -d   # builds the image, starts api + db + pgAdmin
```

First boot auto‑creates the tables (`users`, `vault_items`) and logs
`Application startup complete`.

---

### 4 . Open the services

| URL                                                              | What you get                          | Default creds                        |
| ---------------------------------------------------------------- | ------------------------------------- | ------------------------------------ |
| [http://localhost:8000/register](http://localhost:8000/register) | BlockPass web UI (Jinja2 + Bootstrap) | create your own                      |
| [http://localhost:5050](http://localhost:5050)                   | **pgAdmin 4** database GUI            | email `admin@local.com` / pw `admin` |

> All data live in Docker volume **blockpass\_db\_data** and survive container restarts.
> `docker compose down -v` wipes the volume for a fresh demo.

---

### 5 . Typical workflow

1. **Register** at `/register` (master password = login password).
2. **Login** → redirected to `/vault`.
3. **New Item** → type a title + secret → re‑enter master password.
4. Click the item → re‑enter master password to **reveal**.
5. **Delete** to remove the ciphertext row.

---

### 6 . House‑keeping

| Task                                | Command                        |
| ----------------------------------- | ------------------------------ |
| Stop containers (keep data)         | `docker compose down`          |
| Stop **and** delete all data        | `docker compose down -v`       |
| Follow API logs                     | `docker compose logs -f api`   |
| Rebuild after code or `.env` change | `docker compose up --build -d` |

---

## 🛠️🔐 How the centralized backend works

### 1 . Register → Login flow

| Step                    | What happens                                                                                                                                                                                                                                         | Code                                  |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| **POST /auth/register** | • Pydantic validates `{username,password}`.<br>• `hash_password()` **bcrypt‑12** hashes the password.<br>• Repo stores row with bcrypt hash **plus** a fresh 16‑byte `kdf_salt` and default Argon2id cost parameters (19 MiB mem, 2 passes, 1 lane). | `routes/auth.py` / `core/security.py` |
| **POST /auth/login**    | • Look up user.<br>• bcrypt verifies hash.<br>• Build **JWT** `{sub:user‑id, exp:now+TTL}` signed with `HS256` & `JWT_SECRET`.<br>• Return JSON *and* set an **HttpOnly cookie `access_token`** so HTML works without JavaScript.                    | `routes/auth.py`                      |

---

### 2 . Token auth & vault CRUD

| Piece                       | Behaviour                                                                                                                                                                                  | File(s)                               |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------- |
| **Auth dependency**         | `get_current_user()` checks `Authorization: Bearer` header, else the cookie. It verifies signature & expiry, then loads the user record.                                                   | `core/auth.py`                        |
| **Create item (HTML/JSON)** | Re‑enter master password → Argon2id derives a 256‑bit key (using stored salt & costs) → AES‑256‑GCM encrypts the secret → save `{id (UUID‑hex), user_id, title, data(bytea), created_at}`. | `routes/views.py` & `routes/vault.py` |
| **Read / reveal**           | Same Argon2id run regenerates the key in RAM; AES‑GCM decrypts if tag verifies.                                                                                                            | –                                     |
| **Delete**                  | `POST /vault/{id}/delete` removes the row if `user_id` matches.                                                                                                                            | `routes/views.py` →                   |

---

### 3 . Validation

| Aspect           | Status                                                                            |
| ---------------- | --------------------------------------------------------------------------------- |
| Input validation | All JSON/form bodies pass through Pydantic models (`schemas/*`).                  |
| Route safety     | Every vault query filters by `user_id`; UUID‑hex IDs are unguessable.             |

---

### 4 . Security measures ✅

| Category           | Implementation                                    | Why it matters                                  |
| ------------------ | ------------------------------------------------- | ----------------------------------------------- |
| **Login password** | bcrypt‑12 with unique salt                        | Survives credential dumps & rainbow tables      |
| **Vault key**      | Argon2id (19 MiB, 2×, 1) per user                 | Memory‑hard, quantum margin preserved           |
| **Encryption**     | AES‑256‑GCM (unique nonce, 128‑bit tag)           | Confidentiality **and** integrity               |
| **Zero‑knowledge** | Server stores only ciphertext & public KDF params | DB breach ≠ secret breach                       |
| **Session**        | 60‑min JWT, HttpOnly cookie, SameSite=Lax         | Thwarts XSS token theft, replay window is small |
| **Transport**      | Bring your own TLS proxy (Traefik / NGINX)        | Keeps stack image minimal                       |
| **ORM**            | SQLAlchemy -> prevents SQL injection              | Parameterised queries                           |
| **Dependencies**   | `python:3.12‑slim`; pinned libs                   | Small CVE surface                               |

---

## 🗄️ Database schema

### users

| Column       | Type        | Purpose       |
| ------------ | ----------- | ------------- |
| `id` PK      | serial      | user id       |
| `username`   | varchar     | unique login  |
| `password`   | varchar     | bcrypt string |
| `created_at` | timestamptz | audit         |
| `kdf_salt`   | bytea(16)   | Argon2id salt |
| `kdf_mem`    | int         | 19 456 KiB    |
| `kdf_time`   | int         | 2 passes      |
| `kdf_lanes`  | int         | 1             |

### vault_items

| Column       | Type        | Purpose              |
| ------------ | ----------- | -------------------- |
| `id` PK      | char(32)    | UUID‑hex             |
| `user_id` FK | int         | owner                |
| `title`      | varchar     | plaintext label      |
| `data`       | bytea       | `{nonce,cipher,tag}` |
| `created_at` | timestamptz | audit                |

---

🎉 **You’re all set with centralized mode!**
---

## 🚀 Getting started — Decentralized Mode (IPFS + Ethereum)

### Why Decentralized?

Rather than trusting a single cloud provider, our vault stores encrypted secrets in a peer-to-peer file network (IPFS) and anchors ownership on a public blockchain.  Your AES-256-GCM key never leaves your machine, so only you can decrypt.  Meanwhile, the network ensures availability, integrity, and tamper-evidence—no single operator holds the keys to your data.

---

### 1 . Prerequisites

| Tool / Service                 | Purpose                                               | Installation / Signup                                                 |
| ------------------------------ | ----------------------------------------------------- | --------------------------------------------------------------------- |
| **Git**                        | Clone this repo                                       | [https://git-scm.com/downloads](https://git-scm.com/downloads)        |
| **Python 3.12+ & pip**         | Run the demo script                                   | [https://python.org/downloads](https://python.org/downloads)          |
| **Ape & Ape-Ethereum**         | Compile & deploy smart contracts, send txs on Sepolia | comes with the `requirements.txt` that you will install               |
| **Pinata**                     | Pin encrypted blobs to IPFS without own node          | [https://pinata.cloud/signup](https://pinata.cloud/signup)            |
| **Ethereum wallet (MetaMask)** | Sign transactions & hold test-ETH                     | Install extension & import/generate account                           |
| **Sepolia faucet**             | Fund your wallet with valueless test-ETH              | Search “Sepolia faucet”, paste your address, click “Send me test ETH” |

---

### 2 . Environment Configuration

Create a new `.env` at `BlockPass/dapp/.env` (this file is **git-ignored**):

```dotenv
# ---------------------------------------------------
#  IPFS pinning via Pinata
# ---------------------------------------------------
PINATA_API_KEY=your_pinata_api_key
PINATA_API_SECRET=your_pinata_api_secret

# ---------------------------------------------------
#  Ethereum Sepolia testnet
# ---------------------------------------------------
PRIVATE_KEY=0xabcdef1234…           # your wallet’s private key
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/<PROJECT_ID>

# ---------------------------------------------------
WEB3_WAIT_FOR_RECEIPT_TIMEOUT=300 # used for web3.js to wait for transaction receipt
# ---------------------------------------------------

# ---------------------------------------------------
#  AES key & deployed contract (auto‐generated)
# ---------------------------------------------------
AES_KEY=                           # filled in on first run
VAULT_ADDRESS=                     # filled in on first run
```


| Variable            | Description                                               | Example                                     |
| ------------------- | --------------------------------------------------------- | ------------------------------------------- |
| `PINATA_API_KEY`    | Pinata REST API key                                       | `abc123...`                                 |
| `PINATA_API_SECRET` | Pinata REST API secret                                    | `deadbeef...`                               |
| `PRIVATE_KEY`       | Your Ethereum account’s private key                       | `0xabcdef1234…`                             |
| `SEPOLIA_RPC_URL`   | JSON-RPC endpoint for Sepolia (Infura/Alchemy/PublicNode) | `https://sepolia.infura.io/v3/<PROJECT_ID>` |
| *(auto-generated)*  |                                                           |                                             |
| `AES_KEY`           | Base64-encoded AES-256-GCM key (created on first run)     | *empty*                                     |
| `VAULT_ADDRESS`     | Deployed Vault contract address (written on first run)    | *empty*                                     |

---

### 3 . Installation & Setup

| Step | Command                                                                                               |
| ---- | ----------------------------------------------------------------------------------------------------- |
| 1    | `git clone https://github.com/davv13/BlockPass.git && cd BlockPass/dapp`                              |
| 2    | `python -m venv .venv && source .venv/bin/activate` (macOS/Linux) \| `.\.venv\Scripts\activate` (Win) |
| 3    | `pip install -r requirements.txt`                                                                     |
| 4    | `pip install eth-ape-framework ape-ethereum`                                                          |
| 5    | `source load-env.sh` (macOS/Linux) \| `.\load-env.ps1` (PowerShell)                                   |

---

### 4 . First Run: Bootstrap & Deploy

| Action                              | Description                                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Generate AES key**                | Creates 256-bit key, Base64-encodes it, writes to `AES_KEY` in `.env`.                                  |
| **Compile & Deploy Vault contract** | Sends compiled Solidity to Sepolia, pays gas with test-ETH, writes contract address to `VAULT_ADDRESS`. |
| **Interactive menu**                | Presents options: Create · List · Delete vault items.                                                   |

```bash
ape run scripts/full_flow.py --network ethereum:sepolia
```

---

### 5 . Interactive Workflow

| Command    | User Prompt                            | Behind the Scenes                                                                                                                 |
| ---------- | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Create** | Title → “Email”<br>Secret → “mysecret” | 1. AES-256-GCM encrypt<br>2. Save blob locally<br>3. Pin to IPFS via Pinata → receive CID<br>4. `createItem(CID, title)` on-chain |
| **List**   | —                                      | Calls `getMyItems()` on contract → shows index, title, CID, timestamp                                                             |
| **View**   | Enter index                            | 1. Fetch blob via Pinata<br>2. AES-GCM decrypt locally<br>3. Display plaintext                                                    |
| **Delete** | Enter index                            | 1. `deleteItem(index)` on-chain<br>2. Unpin CID via Pinata API                                                                    |

---

### 6 . Sepolia Testnet Deep Dive

| Aspect               | Sepolia (Testnet)                                | Mainnet (Production)              |
| -------------------- | ------------------------------------------------ | --------------------------------- |
| **Value of ETH**     | Valueless tokens—free from faucets               | Real economic value               |
| **Acquiring ETH**    | Public faucets (on-chain transfer of test-ETH)   | Purchase from exchanges           |
| **Network security** | Fewer nodes → periodic outages, possible re-orgs | Highly decentralized, very secure |
| **Block times**      | Variable, sometimes faster/slower than mainnet   | \~12–14 sec per block             |
| **API endpoints**    | `SEPOLIA_RPC_URL`                                | `MAINNET_RPC_URL`                 |
| **Gas costs**        | Paid in test-ETH (refill via faucets)            | Paid in real ETH                  |

---

### 7 . IPFS Pinning via Pinata

| Feature         | Description                                                                    |
| --------------- | ------------------------------------------------------------------------------ |
| **Pinning**     | Guarantees your CIDs stay replicated and online on Pinata’s IPFS nodes         |
| **Redundancy**  | Multiple regions & nodes, configurable replication                             |
| **Dashboard**   | Visualize pinned CIDs, remove pins, monitor usage                              |
| **Integration** | Use HTTP API with `PINATA_API_KEY` & `PINATA_API_SECRET` (never commit these!) |

---

### 8 . Security Considerations

| Category             | Implementation                                          | Why It Matters                                          |
| -------------------- | ------------------------------------------------------- | ------------------------------------------------------- |
| **Symmetric crypto** | AES-256-GCM with per-blob nonce & 128-bit tag           | Confidentiality + integrity                             |
| **Key storage**      | AES key only in local `.env` (not on IPFS or chain)     | Prevents key exfiltration                               |
| **Private key**      | User’s Ethereum key in `.env` or hardware wallet config | Custodial control, avoid reuse in multiple environments |
| **Contract code**    | Immutable once deployed—audit Solidity before Mainnet   | Prevents logic bugs, reentrancy attacks                 |
| **Environment**      | `.env` in `.gitignore`, encrypted disk recommended      | Protect secrets from accidental commits or local theft  |
| **Transport**        | All IPFS & RPC calls over HTTPS                         | Protects against network eavesdropping                  |

---

🎉 **You’re all set with decentralized mode!**
---


