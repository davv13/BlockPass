from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.repository.base import UserRepository
from app.models.user import User

class PostgresRepo(UserRepository):
    def _session(self) -> Session:
        return SessionLocal()

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