# app/core/security.py

from datetime import datetime, timedelta
from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.repository import pick_repo

# password‑hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# load .env‑driven settings
settings = get_settings()

# this is the scheme we wired into OpenAPI:
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: Dict[str, str], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> str:
    """
    Decode the JWT and return the `sub` (user ID) claim.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return sub
    except JWTError:
        raise credentials_exception

async def get_current_user(user_id: str = Depends(oauth2_scheme)):
    """
    Dependency to pull your user out of the token.
    `user_id` here is actually the JWT `sub` claim.
    """
    # decode_token will raise 401 if invalid
    sub = decode_token(user_id)
    user = pick_repo().get_by_id(sub)
    if not user:
        raise credentials_exception
    return user
