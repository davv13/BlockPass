# app/repository/pg_repo.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.repository.base import UserRepository
from app.models.user import User
from app.models.vault import VaultItem as VaultModel


class PostgresRepo(UserRepository):
    def _session(self) -> Session:
        return SessionLocal()

    # --- user methods ---
    def create_user(self, username: str, hashed_pw: str):
        with self._session() as db:
            if db.query(User).filter_by(username=username).first():
                raise ValueError("exists")
            user = User(username=username, password=hashed_pw)
            db.add(user)
            db.commit()
            db.refresh(user)
            return {"id": user.id, "username": user.username}

    def get_by_username(self, username: str):
        with self._session() as db:
            rec = db.query(User).filter_by(username=username).first()
            if rec:
                return {"id": rec.id, "username": rec.username, "password": rec.password}
            return None

    # --- vault methods ---
    def create_item(self, user_id: int, title: str, ciphertext: bytes) -> VaultModel:
        with self._session() as db:
            item = VaultModel(user_id=user_id, title=title, data=ciphertext)
            db.add(item)
            db.commit()
            db.refresh(item)
            return item

    def list_items(self, user_id: int) -> List[VaultModel]:
        with self._session() as db:
            return db.query(VaultModel).filter_by(user_id=user_id).all()

    def get_item(self, user_id: int, item_id: int) -> Optional[VaultModel]:
        with self._session() as db:
            return (
                db.query(VaultModel)
                  .filter_by(user_id=user_id, id=item_id)
                  .first()
            )
        
    # in PostgresRepo (app/repository/pg_repo.py)
    def get_by_id(self, id: str):
        with self._session() as db:
            rec = db.query(User).get(id)
            if rec:
                return {"id": rec.id, "username": rec.username, "password": rec.password}
        return None
