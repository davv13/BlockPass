from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserOut, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.repository import pick_repo

router = APIRouter(prefix="/auth", tags=["Auth"])
repo = pick_repo()  # chosen at import time

@router.post("/register", response_model=UserOut)
def register(user: UserCreate):
    try:
        created = repo.create_user(user.username, hash_password(user.password))
        return created
    except ValueError:
        raise HTTPException(status_code=400, detail="Username already exists")

@router.post("/login", response_model=Token)
def login(user: UserCreate):
    record = repo.get_by_username(user.username)
    if not record or not verify_password(user.password, record["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": record["username"]})
    return {"access_token": token, "token_type": "bearer"}