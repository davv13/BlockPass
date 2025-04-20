# app/schemas/user.py
from pydantic import BaseModel, ConfigDict

# ----- incoming payload -----
class UserCreate(BaseModel):
    username: str
    password: str

# ----- outgoing user -----
class UserOut(BaseModel):
    id: int          # ← was str
    username: str
    model_config = ConfigDict(from_attributes=True)

# ----- login response (JWT) -----
class Token(BaseModel):
    access_token: str
    token_type: str