# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserCreate, UserOut, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.core import kdf                          # ← NEW
from app.repository import pick_repo

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
def register(user: UserCreate):
    """
    1.  Hash the password with bcrypt (login auth).
    2.  Generate a unique Argon2id salt for this user.
    3.  Store salt + default KDF params in the user record.
    """
    repo = pick_repo()

    pwd_hash = hash_password(user.password)     # bcrypt‑12
    salt     = kdf.generate_salt()              # 16‑byte random salt

    try:
        new = repo.create_user(
            username=user.username,
            hashed_pw=pwd_hash,
            kdf_salt=salt,                      # per‑user KDF info
            # kdf_mem / time / lanes keep their defaults (19 MiB, 2, 1)
        )
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
    """
    Login flow stays the same—bcrypt for authentication,
    Argon2id is only used later when encrypting/decrypting vault items.
    """
    repo = pick_repo()
    user = repo.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    access_token = create_access_token({"sub": str(user["id"])})
    return {"access_token": access_token, "token_type": "bearer"}
