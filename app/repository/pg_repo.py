# app/repository/pg_repo.py
import datetime, uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.repository.base import UserRepository
from app.models.user import User
from app.models.vault import VaultItem as VaultModel


class PostgresRepo(UserRepository):
    # ─────────────────── internal ──────────────────────────────────────
    def _session(self) -> Session:            # little helper to open a DB
        return SessionLocal()

    # ─────────────────── user section ──────────────────────────────────
    def create_user(self, username: str, hashed_pw: str) -> dict:
        with self._session() as db:
            if db.query(User).filter_by(username=username).first():
                raise ValueError("exists")
            user = User(username=username, password=hashed_pw)
            db.add(user)
            db.commit()
            db.refresh(user)
            return {"id": str(user.id), "username": user.username}

    def get_by_username(self, username: str) -> Optional[dict]:
        with self._session() as db:
            rec = db.query(User).filter_by(username=username).first()
            if not rec:
                return None
            return {
                "id": str(rec.id),
                "username": rec.username,
                "password": rec.password,
            }

    def get_by_id(self, user_id: str) -> Optional[dict]:
        with self._session() as db:
            rec = db.get(User, int(user_id))
            if not rec:
                return None
            return {
                "id": str(rec.id),
                "username": rec.username,
                "password": rec.password,
            }

    # ─────────────────── vault‑item section ────────────────────────────
    def create_item(
        self,
        user_id: str,
        title: str,
        ciphertext: bytes
    ) -> VaultModel:
        with self._session() as db:
            new = VaultModel(
                # id=uuid.uuid4().hex,
                user_id=int(user_id),                      # FK is integer
                title=title,
                data=ciphertext,
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

    def get_item(
        self,
        user_id: str,
        item_id: str
    ) -> Optional[VaultModel]:
        with self._session() as db:
            return (
                db.query(VaultModel)
                .filter_by(user_id=int(user_id), id=item_id)
                .first()
            )