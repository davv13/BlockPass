from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database.base import Base
import uuid

class VaultItem(Base):
    __tablename__ = "vault_items"

    id = Column(
        String(32),
        primary_key=True,
        default=lambda: uuid.uuid4().hex,
        unique=True,
        index=True,
    )
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    data = Column(LargeBinary, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )