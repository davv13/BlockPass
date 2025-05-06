## 🔐 BlockPass - Secure Password Manager

(Centralized mode + upcoming Blockchain mode)\*\*

A study project that shows how a *classic* backend can reach modern “zero‑knowledge” guarantees (per‑user Argon2id, AES‑256‑GCM, short‑lived JWT) before we port the same UX to a decentralized IPFS + block‑chain design.

---

## 🚀 Getting started — Centralized stack (Docker Compose, PostgreSQL)

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

