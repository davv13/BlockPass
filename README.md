# **BlockPass Quick‑Start Guide**

This guide shows you how to get **BlockPass** running in two modes:

1. **File‑backend mode** (no Docker, stores users in a JSON file)  
2. **Docker + Postgres mode** (containerized Postgres database + optional pgAdmin)

Follow the sections below in order. You can skip one mode if you only need the other.

---

## 🚀 Prerequisites

- **Git**  
- **Python 3.11+**  
- **pip** (comes with Python)  
- **Docker Desktop** (for Docker mode)  
- (Optional) **pgAdmin 4** or another Postgres GUI  

---

## A) File‑backend Mode

Stores registered users in a local JSON file—no database or Docker required.

### 1. Clone & enter repo
```bash
git clone https://github.com/yourusername/BlockPass.git
cd BlockPass
```

### 2. Create & activate a virtual environment
```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\activate
# (macOS/Linux)
# source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create your `.env` file
In the project root, create a file named `.env` with these contents:
```ini
DB_BACKEND=file
FILE_PATH=./blockpass_users.json

JWT_SECRET=supersecretkey123
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 5. Verify built‑in Swagger is enabled
Ensure in `app/main.py` you have:
```python
app = FastAPI(
    # … metadata …,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
)
```
and **no** custom `/docs` override.

### 6. Start the server
```bash
uvicorn app.main:app --reload
```
You should see:
```
Uvicorn running on http://127.0.0.1:8000
```
A new file `blockpass_users.json` (containing `[]`) will appear in the root.

### 7. Smoke‑test endpoints
- **Ping**  
  ```bash
  curl http://127.0.0.1:8000/ping
  # → {"msg":"pong"}
  ```
- **OpenAPI JSON**  
  ```bash
  curl http://127.0.0.1:8000/openapi.json -o spec.json
  # spec.json is created immediately
  ```

### 8. Use Swagger UI
Open your browser to **http://127.0.0.1:8000/docs**. You’ll see:

- **POST /auth/register**  
- **POST /auth/login**

### 9. Register & verify
1. In Swagger, **POST /auth/register** with:
   ```json
   { "username": "alice", "password": "secret" }
   ```
2. You get back:
   ```json
   { "id": "UUID‑string", "username": "alice" }
   ```
3. Inspect `blockpass_users.json`—it now contains your user entry.
4. **POST /auth/login** with the same body to receive a JWT.

---

## B) Docker + Postgres Mode

Runs Postgres, your FastAPI app, and pgAdmin (optional) in containers.

### 1. Switch `.env` to Postgres
Update your existing `.env` with:
```ini
DB_BACKEND=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=blockpass
POSTGRES_HOST=db
POSTGRES_PORT=5432

JWT_SECRET=supersecretkey123
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 2. Verify `docker-compose.yml`
Ensure under `services:` you have three entries:

- **db** (Postgres)
- **api** (your FastAPI app)
- **pgadmin** (dpage/pgadmin4)

And that indentation is correct.

### 3. Build & start containers
```bash
docker compose build api
docker compose up -d
```

### 4. Confirm services are running
```bash
docker compose ps
```
You should see:
```
blockpass-db-1      Up (healthy)   0.0.0.0:5432->5432/tcp
blockpass-api-1     Up             0.0.0.0:8000->8000/tcp
blockpass-pgadmin-1 Up             0.0.0.0:5050->80/tcp
```

### 5. Smoke‑test API
```bash
curl http://localhost:8000/ping       # → {"msg":"pong"}
curl http://localhost:8000/openapi.json -o spec.json
```

### 6. Use Swagger UI
Open **http://localhost:8000/docs**, then:

1. **POST /auth/register**  
   ```json
   { "username": "bob", "password": "hunter2" }
   ```
   → returns  
   ```json
   { "id": 1, "username": "bob" }
   ```
2. **POST /auth/login**  
   → returns a JWT

### 7. Inspect Postgres via psql
```bash
docker compose exec db psql -U postgres -d blockpass
# at psql> prompt:
\dt
SELECT * FROM users;
```

### 8. (Optional) Inspect via pgAdmin
1. Open **http://localhost:5050**, log in with **admin@local.com** / **admin**  
2. Register server:  
   - Host: `db`  
   - Port: `5432`  
   - DB: `blockpass`  
   - User/Pass: `postgres`  
3. Expand **Schemas → public → Tables → users** → **View/Edit Data → All Rows**

---
