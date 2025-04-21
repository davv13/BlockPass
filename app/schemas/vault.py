from pydantic import BaseModel
from datetime import datetime
from typing import Union

class VaultItemCreate(BaseModel):
    title: str
    secret: str

class VaultItemOut(BaseModel):
    id: Union[int, str] 
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}

class VaultItemDetail(VaultItemOut):
    secret: str