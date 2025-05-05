from sqlalchemy import Column, Integer, String, DateTime, func
from app.database.base import Base
from sqlalchemy import Column, LargeBinary, Integer

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
        # NEW ↓
    kdf_salt    = Column(LargeBinary(16), nullable=False)
    kdf_mem     = Column(Integer, default=19 * 1024)     # kibibytes → 19 MiB
    kdf_time    = Column(Integer, default=2)             # iterations
    kdf_lanes   = Column(Integer, default=1)             # parallelism
