# app/schemas/user.py
from typing import Union
from pydantic import BaseModel, ConfigDict

# ----- incoming payload for registration/login -----
class UserCreate(BaseModel):
    username: str
    password: str

# ----- outgoing user representation -----
class UserOut(BaseModel):
    id: Union[int, str]  # allow Postgres int or file‑backend UUID
    username: str

    # Pydantic v2: allow attribute access
    model_config = ConfigDict(from_attributes=True)

# ----- JWT token response schema -----
class Token(BaseModel):
    access_token: str
    token_type: str