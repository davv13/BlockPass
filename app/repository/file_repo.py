# app/repository/file_repo.py
import json
import threading
import uuid
import datetime
from pathlib import Path
from typing import Optional, List

from app.repository.base import UserRepository
from app.models.vault import VaultItem as VaultModel
from app.core import kdf                              # ← NEW
from app.core.config import get_settings

settings = get_settings()


class FileRepo(UserRepository):
    def __init__(self, path: str | None = None):
        self.path = Path(path or "./blockpass_users.json")
        self._lock = threading.Lock()
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    # ───────────────────────── private helpers ──────────────────────────
    def _load(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data):
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ───────────────────────── UserRepository API ───────────────────────
    def create_user(
        self,
        username: str,
        hashed_pw: str,
        *,
        kdf_salt: bytes | None = None,
        kdf_mem: int = 19 * 1024,  # KiB  ≈ 19 MiB
        kdf_time: int = 2,
        kdf_lanes: int = 1,
    ) -> dict:
        """
        Create a user record with unique Argon2id parameters.
        The salt is stored as hex to keep JSON human‑readable.
        """
        with self._lock:
            data = self._load()
            if any(u["username"] == username for u in data):
                raise ValueError("exists")

            if kdf_salt is None:
                kdf_salt = kdf.generate_salt()

            user = {
                "id": str(uuid.uuid4()),
                "username": username,
                "password": hashed_pw,           # bcrypt hash for login
                # ↓ Argon2id vault‑key parameters
                "kdf_salt": kdf_salt.hex(),
                "kdf_mem": kdf_mem,
                "kdf_time": kdf_time,
                "kdf_lanes": kdf_lanes,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            data.append(user)
            self._save(data)
            # never return hashed pw or KDF salt to the caller
            return {"id": user["id"], "username": user["username"]}

    def get_by_username(self, username: str) -> Optional[dict]:
        return next((u for u in self._load() if u["username"] == username), None)

    def get_by_id(self, user_id: str) -> Optional[dict]:
        return next((u for u in self._load() if u["id"] == user_id), None)

    # ───────────────────────── Vault methods ────────────────────────────
    def _load_items_path(self) -> Path:
        # items live in a separate file beside the user DB
        return self.path.with_name("blockpass_vault.json")

    def _load_items(self) -> list:
        p = self._load_items_path()
        if not p.exists():
            p.write_text("[]", encoding="utf-8")
        return [VaultModel(**i) for i in json.loads(p.read_text())]

    def _save_items(self, items: list):
        p = self._load_items_path()
        p.write_text(json.dumps([i.dict() for i in items], indent=2))

    def create_item(self, user_id: str, title: str, ciphertext: str) -> VaultModel:
        """ciphertext is the JSON blob returned by app.core.encryption.encrypt()"""
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
            (i for i in self._load_items() if i.user_id == user_id and i.id == item_id),
            None
        )
    
    def delete_item(self, user_id: str, item_id: str) -> None:
        items = self._load_items()
        filtered = [i for i in items if not (i.user_id == user_id and i.id == item_id)]
        self._save_items(filtered)

