# app/core/auth.py
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional

from app.core.config import get_settings
from app.repository import pick_repo

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_token(
    request: Request,
    header_token: Optional[str] = Depends(oauth2_scheme),
) -> str:
    """
    Prefer the Authorization header; fall back to the `access_token`
    cookie which now holds the *raw* JWT.
    """
    if header_token:
        return header_token

    cookie_val = request.cookies.get("access_token")
    if cookie_val:
        return cookie_val            # <- raw JWT (no Bearer prefix)

    raise credentials_exception


def get_current_user(token: str = Depends(get_token)):
    print(">>> get_current_user(): raw token from request =", repr(token))  # DEBUG

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.ALGORITHM],
        )
        print(">>> payload decoded OK =", payload)                          # DEBUG
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError as ex:
        print("!!! jwt.decode FAILED:", ex)                                 # DEBUG
        raise credentials_exception

    user = pick_repo().get_by_id(user_id)
    print(">>> repo.get_by_id() returned:", user)                           # DEBUG
    if not user:
        raise credentials_exception
    return user
