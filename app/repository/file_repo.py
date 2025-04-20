import json, os, threading, uuid, datetime
from pathlib import Path
from app.repository.base import UserRepository
from app.core.config import get_settings

settings = get_settings()

class FileRepo(UserRepository):
    def __init__(self, path: str | None = None):
        self.path = Path(path or "./blockpass_users.json")
        self._lock = threading.Lock()
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    # internal helpers
    def _load(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data):
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # interface methods
    def create_user(self, username: str, hashed_pw: str):
        with self._lock:
            data = self._load()
            if any(u["username"] == username for u in data):
                raise ValueError("exists")
            user = {
                "id": str(uuid.uuid4()),
                "username": username,
                "password": hashed_pw,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            data.append(user)
            self._save(data)
            return {"id": user["id"], "username": user["username"]}

    def get_by_username(self, username: str):
        data = self._load()
        return next((u for u in data if u["username"] == username), None)