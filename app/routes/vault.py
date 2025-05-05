# app/routes/vault.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core import kdf, encryption
from app.repository import pick_repo
from app.routes.auth import login  # JWT dependency if you have one
from typing import List

router = APIRouter(prefix="/vault", tags=["Vault"])

class SecretIn(BaseModel):
    master_password: str
    title: str
    secret_value: str

class SecretOut(BaseModel):
    id: str
    title: str
    secret_value: str

@router.post("/", response_model=SecretOut, status_code=201)
def create_secret(payload: SecretIn, user_id: str = Depends(login)):
    repo = pick_repo()
    user = repo.get_by_id(user_id)

    if not user:
        raise HTTPException(404, "User not found")

    # 1) derive per‑user vault key
    key = kdf.derive_key(
        master_pwd=payload.master_password,
        salt=bytes.fromhex(user["kdf_salt"]),
        mem_kib=user["kdf_mem"],
        time=user["kdf_time"],
        lanes=user["kdf_lanes"],
    )

    try:
        blob = encryption.encrypt(payload.secret_value, key)
    finally:
        del key  # secure wipe

    item = repo.create_item(user_id, payload.title, blob)
    return {"id": item.id, "title": item.title, "secret_value": payload.secret_value}


class SecretFetchIn(BaseModel):
    master_password: str

@router.get("/{item_id}", response_model=SecretOut)
def get_secret(item_id: str, query: SecretFetchIn = Depends(), user_id: str = Depends(login)):
    repo = pick_repo()
    user  = repo.get_by_id(user_id)
    item  = repo.get_item(user_id, item_id)

    if not item:
        raise HTTPException(404, "Secret not found")

    key = kdf.derive_key(
        master_pwd=query.master_password,
        salt=bytes.fromhex(user["kdf_salt"]),
        mem_kib=user["kdf_mem"],
        time=user["kdf_time"],
        lanes=user["kdf_lanes"],
    )

    try:
        plaintext = encryption.decrypt(item.data, key)
    finally:
        del key

    return {"id": item.id, "title": item.title, "secret_value": plaintext}
