# app/repository/pg_repo.py
import datetime
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.repository.base import UserRepository
from app.models.user import User
from app.models.vault import VaultItem as VaultModel
from app.core import kdf                                 # ← NEW


class PostgresRepo(UserRepository):
    # ─────────────────── internal ──────────────────────────────────────
    def _session(self) -> Session:
        """Return a new SQLAlchemy session."""
        return SessionLocal()

    # ─────────────────── user section ──────────────────────────────────
    def create_user(
        self,
        username: str,
        hashed_pw: str,
        *,
        kdf_salt: bytes | None = None,
        kdf_mem: int = 19 * 1024,  # KiB ≈ 19 MiB
        kdf_time: int = 2,
        kdf_lanes: int = 1,
    ) -> dict:
        """
        Insert a new user with per‑user Argon2id parameters.
        If no salt is provided, generate one.
        """
        if kdf_salt is None:
            kdf_salt = kdf.generate_salt()

        with self._session() as db:
            if db.query(User).filter_by(username=username).first():
                raise ValueError("exists")

            user = User(
                username=username,
                password=hashed_pw,        # bcrypt hash for login
                kdf_salt=kdf_salt,
                kdf_mem=kdf_mem,
                kdf_time=kdf_time,
                kdf_lanes=kdf_lanes,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            return {"id": str(user.id), "username": user.username}

    def get_by_username(self, username: str) -> Optional[dict]:
        with self._session() as db:
            rec: User | None = db.query(User).filter_by(username=username).first()
            if not rec:
                return None
            return {
                "id":         str(rec.id),
                "username":   rec.username,
                "password":   rec.password,
                "kdf_salt":   rec.kdf_salt.hex(),
                "kdf_mem":    rec.kdf_mem,
                "kdf_time":   rec.kdf_time,
                "kdf_lanes":  rec.kdf_lanes,
            }

    def get_by_id(self, user_id: str) -> Optional[dict]:
        with self._session() as db:
            rec: User | None = db.get(User, int(user_id))
            if not rec:
                return None
            return {
                "id":         str(rec.id),
                "username":   rec.username,
                "password":   rec.password,
                "kdf_salt":   rec.kdf_salt.hex(),
                "kdf_mem":    rec.kdf_mem,
                "kdf_time":   rec.kdf_time,
                "kdf_lanes":  rec.kdf_lanes,
            }

    # ─────────────────── vault‑item section ────────────────────────────
    def create_item(
        self,
        user_id: str,
        title: str,
        ciphertext: str,          # AES‑GCM blob as JSON string
    ) -> VaultModel:
        with self._session() as db:
            new = VaultModel(
            id=uuid.uuid4().hex,
            user_id=int(user_id),
            title=title,
            # JSON string → UTF-8 bytes for LargeBinary column
            data=ciphertext.encode("utf-8"),
            created_at=datetime.datetime.utcnow(),
        )
            db.add(new)
            db.commit()
            db.refresh(new)
            return new

    def list_items(self, user_id: str) -> List[VaultModel]:
        with self._session() as db:
            return (
                db.query(VaultModel)
                .filter_by(user_id=int(user_id))
                .order_by(VaultModel.created_at.desc())
                .all()
            )

    def get_item(self, user_id: str, item_id: str) -> Optional[VaultModel]:
        with self._session() as db:
            return (
                db.query(VaultModel)
                .filter_by(user_id=int(user_id), id=item_id)
                .first()
            )
        

        # ─────────────────── vault-item deletion ─────────────────────────────
    def delete_item(self, user_id: str, item_id: str) -> None:
        """
        Delete the vault item with that id for the given user.
        """
        with self._session() as db:
            obj = (
                db.query(VaultModel)
                  .filter_by(user_id=int(user_id), id=item_id)
                  .first()
            )
            if not obj:
                return  # or raise ValueError("Not found")
            db.delete(obj)
            db.commit()

