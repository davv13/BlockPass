from app.core.config import get_settings
from app.repository.file_repo import FileRepo

def pick_repo():
    backend = get_settings().DB_BACKEND.lower()
    if backend == "file":
        return FileRepo()
    elif backend == "postgres":
        from app.repository.pg_repo import PostgresRepo
        return PostgresRepo()
    else:
        raise RuntimeError(f"Unsupported backend: {backend}")
from app.core.config import get_settings
from app.repository.file_repo import FileRepo

def pick_repo():
    backend = get_settings().DB_BACKEND.lower()
    if backend == "file":
        return FileRepo()
    elif backend == "postgres":
        from app.repository.pg_repo import PostgresRepo
        return PostgresRepo()
    else:
        raise RuntimeError(f"Unsupported backend: {backend}")