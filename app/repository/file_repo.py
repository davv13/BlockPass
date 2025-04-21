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
    def __init__(self, path: Optional[str] = None):
        # user storage
        self.path = Path(path or settings.FILE_PATH)
        self._lock = threading.Lock()
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("[]", encoding="utf-8")

        # vault‐item storage (separate file)
        self.vault_path = self.path.parent / "blockpass_items.json"
        if not self.vault_path.exists():
            self.vault_path.write_text("[]", encoding="utf-8")

    # ─── internal helpers ──────────────────────────────────────────────────
    def _load(self) -> List[dict]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data: List[dict]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_items(self) -> List[VaultModel]:
        raw = json.loads(self.vault_path.read_text(encoding="utf-8"))
        # rehydrate into VaultModel objects
        return [
            VaultModel(
                id=item["id"],
                user_id=item["user_id"],
                title=item["title"],
                data=bytes.fromhex(item["data"]),
                created_at=datetime.datetime.fromisoformat(item["created_at"])
            )
            for item in raw
        ]

    def _save_items(self, items: List[VaultModel]) -> None:
        raw = []
        for i in items:
            raw.append({
                "id": i.id,
                "user_id": i.user_id,
                "title": i.title,
                "data": i.data.hex(),
                "created_at": i.created_at.isoformat()
            })
        self.vault_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

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

    def get_by_id(self, id: str) -> Optional[dict]:
        # ←— this was missing!
        return next((u for u in self._load() if u["id"] == id), None)

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