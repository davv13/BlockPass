# app/repository/file_repo.py

import json
import threading
import uuid
import datetime
from pathlib import Path
from typing import Optional, List

from app.repository.base import UserRepository
from app.models.vault import VaultItem as VaultModel
from app.core.config import get_settings

settings = get_settings()

class FileRepo(UserRepository):
    def __init__(self, path: str | None = None):
        self.path = Path(path or "./blockpass_users.json")
        self._lock = threading.Lock()
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _load(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data):
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

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

    def get_by_id(self, user_id: str):
        data = self._load()
        u = next((u for u in data if u["id"] == user_id), None)
        if not u:
            return None
        return {"id": u["id"], "username": u["username"], "password": u["password"]}
    
    # ─── UserRepository methods ───────────────────────────────────────────
    def create_user(self, username: str, hashed_pw: str) -> dict:
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

    def get_by_username(self, username: str) -> Optional[dict]:
        return next((u for u in self._load() if u["username"] == username), None)

    def get_by_id(self, user_id: str) -> dict | None:
        data = self._load()
        return next((u for u in data if u["id"] == user_id), None)

    # ─── Vault methods ─────────────────────────────────────────────────────
    def create_item(self, user_id: str, title: str, ciphertext: bytes) -> VaultModel:
        items = self._load_items()
        new = VaultModel(
            id=uuid.uuid4().hex,
            user_id=user_id,
            title=title,
            data=ciphertext,
            created_at=datetime.datetime.utcnow()
        )
        items.append(new)
        self._save_items(items)
        return new

    def list_items(self, user_id: str) -> List[VaultModel]:
        return [i for i in self._load_items() if i.user_id == user_id]

    def get_item(self, user_id: str, item_id: str) -> Optional[VaultModel]:
        return next(
            (i for i in self._load_items()
             if i.user_id == user_id and i.id == item_id),
            None
        )