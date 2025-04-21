# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserCreate, UserOut, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.repository import pick_repo

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
def register(user: UserCreate):
    repo = pick_repo()
    try:
        new = repo.create_user(user.username, hash_password(user.password))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    return new

@router.post(
    "/login",
    response_model=Token,
    summary="Obtain a JWT token",
)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    repo = pick_repo()
    user = repo.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    access_token = create_access_token({"sub": str(user["id"])})
    return {"access_token": access_token, "token_type": "bearer"}