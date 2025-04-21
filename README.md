## 🔐 **Secure Password Manager (Centralized + Blockchain-based)**

### The goal is to build a secure password management system with two modes — one using a traditional backend, and another using a decentralized blockchain approach.

---

## 🚀 Getting Started with the Centralized Mode — PostgreSQL backend (Docker Compose)

### Prerequisites
| tool | why you need it | get it |
|------|-----------------|--------|
| **Git** | clone the repo | <https://git‑scm.com> |
| **Docker Engine + Docker Compose** | run PostgreSQL, the FastAPI app & pgAdmin in containers | <https://docs.docker.com/get-docker> |

---

### 1 . Clone the repo
```bash
git clone https://github.com/<your‑user>/BlockPass.git
cd BlockPass
```

---

### 2 . Create `.env`

> `.env` is **git‑ignored** on purpose – each user keeps secrets locally.

```bash
touch .env
```

Paste the following **minimal** configuration (edit to taste):

```dotenv
################  Database  ################
DB_BACKEND=postgres              # ← tell the app to use PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres       # change!!!
POSTGRES_DB=blockpass
POSTGRES_HOST=db                 # ← name of the service in docker‑compose.yml
POSTGRES_PORT=5432

################  JWT  ################
JWT_SECRET=supersecretkey123     # change!!!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

################  Vault  ################
# 32‑byte key – see step 2‑b to generate safely
VAULT_KEY=IgFtNNlpDrUbMEMlz6qVq5Bucr7iF9SakRiO3MYOqUU=
```

#### 2‑b . Generate a strong `VAULT_KEY`
```bash
python - <<'PY'
import secrets, base64
print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())
PY
```
Copy the printed string into `VAULT_KEY=`.

---

### 3 . Build & run everything

```bash
docker compose up --build -d     # builds the API image and starts api + db + pgAdmin
```

**First run = first migrations**  
On launch the API auto‑creates all tables inside `blockpass` database.

---

### 4 . Open the services

| URL | what you get | default creds |
|-----|--------------|---------------|
| <http://localhost:8000> | BlockPass web UI (Jinja2 + Bootstrap) | register your own |
| <http://localhost:5050>  | **pgAdmin 4** | *email*: `admin@local.com`  /  *password*: `admin` |

> **Note:** data lives in the Docker volume `blockpass_db-data`; it persists across container restarts.

---

### 5 . Typical workflow

1. **Register** a user at `http://localhost:8000/register`.  
2. **Login** → you’re redirected to `/vault`.  
3. Add, view & decrypt password items right in the browser.

---

### 6 . House‑keeping commands

| task | command |
|------|---------|
| Stop containers (keep data) | `docker compose down` |
| Stop **and** wipe the database | `docker compose down -v` |
| Watch live API logs | `docker compose logs -f api` |
| Rebuild after code or `.env` change | `docker compose up --build -d` |

---

## 🛠️🔐 How the backend of PostgreSQL backend (Docker Compose) works – under the hood  



### 1 . User **Register → Login** flow & password handling

| step | what happens | relevant code |
|------|--------------|---------------|
| **POST /​auth/register** | *a)* JSON payload `{username, password}` is parsed by Pydantic.<br>*b)* `app/core/security.hash_password()` hashes the raw password with **bcrypt $2b$12** (12 work‑factor).<br>*c)* The repository stores `{id, username, password_hash}`.<br>*d)* On success → **201 Created**. | `routes/auth.py` → `security.py` |
| **POST /​auth/login** | *a)* Load user by `username`.<br>*b)* **bcrypt verify** against stored hash.<br>*c)* On match → build a **JWT** ⚙️: `{ "sub": <user‑id>, "exp": <now + n min> }` signed with `HS256` & `JWT_SECRET`.<br>*d)* Return it two ways: JSON → `{"access_token": "…"}` **and** set an **httpOnly cookie `access_token`** so the HTML UI works without JS. | `routes/auth.py` |

**Storage:**  

* **PostgreSQL backend** → row in `users` table. Column `password` stores the bcrypt string (`$2b$12$…`).  
* **File backend** → same fields in `blockpass_users.json`.

---

### 2 . Token‑based auth (JWT) & CRUD for vault entries

| piece | behaviour | file(s) |
|-------|-----------|---------|
| **Auth dependency** | `get_current_user()` first tries **`Authorization: Bearer <jwt>`**, then falls back to the cookie. It decodes the token, verifies signature & expiry and loads the user. `401` otherwise. | `core/auth.py` |
| **Create item** | **POST /​vault/create** (HTML) or **POST /​vault/** (JSON) → encrypt secret with Fernet (key =`VAULT_KEY`) → store `{id (UUID‑hex), user_id, title, data (cipher‑text), created_at}`. | `routes/views.py` + `routes/vault.py` |
| **Read list / item** | Only rows whose `user_id` == current user are queried; secret is decrypted on demand. | same as above |
| **Update / Delete** | not implemented yet – deliberately MVP. (Good first issue ≙ PATCH/DELETE endpoints + HTML) |

---

### 3 . Validation, sanitation, tests

| aspect | status |
|--------|--------|
| **Input validation** | All incoming JSON / form bodies pass through **Pydantic models** (`schemas/*.py`). |
| **Route sanitation** | Vault routes verify ownership before returning data; IDs are URL‑safe strings (hex). |
| **Hashing & token unit tests** | Basic pytest suite in `tests/test_security.py` – covers `hash_password()`, `verify_password()` and `create_access_token()` round‑trip. (_Run `pytest -q` locally_). |

---

### 4 . Security measures already in place ✅

| category | what we do | why it matters |
|----------|------------|----------------|
| **Password safety** | * bcrypt‑12 with per‑user salt <br>* never store plaintext | Defends against credential dumps & rainbow tables |
| **Transport** | The stack itself is TLS‑agnostic → put **Traefik / NGINX TLS termination** in front when deploying. |
| **Authentication** | * Short‑lived JWT (default 60 min) <br>* Stored in **httpOnly** cookie → immune to XSS JS theft. | Minimises token leakage vector. |
| **Authorisation** | Every vault query filters by `user_id`. Users can’t touch others’ items. |
| **Data‑at‑rest** | Vault secrets are **AES‑256‑GCM via Fernet** with a key nobody but the operator knows (`VAULT_KEY`). |
| **Dependency safety** | Latest stable libs in `requirements.txt`; image is **python:3.13‑slim** to keep CVE surface small. |
| **CSRF** | Safe for same‑site cookies (`SameSite=Lax` by default in FastAPI). |
| **SQL injection** | All queries use SQLAlchemy ORM or parameterised drivers – no string concatenation. |

---