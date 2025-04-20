from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.database.base import Base

settings = get_settings()

# Decide which storage engine to build
if settings.DB_BACKEND == "postgres":
    URL = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    engine = create_engine(URL, pool_pre_ping=True)
elif settings.DB_BACKEND == "sqlite":
    URL = f"sqlite:///{settings.SQLITE_PATH}"
    engine = create_engine(
        URL, connect_args={"check_same_thread": False}
    )
else:                       # file backend ⇒ no SQL engine
    engine = None

# Only create a Session factory if we actually have an engine
SessionLocal = (
    sessionmaker(bind=engine, autocommit=False, autoflush=False) if engine else None
)
