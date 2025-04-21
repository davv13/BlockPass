# app/routes/vault.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas.vault import VaultItemCreate, VaultItemOut, VaultItemDetail
from app.core.security import get_current_user
from app.repository import pick_repo
from app.core.crypto import encrypt, decrypt

router = APIRouter(prefix="/vault", tags=["Vault"])

@router.post("/", response_model=VaultItemOut, status_code=201)
def create_vault_item(
    payload: VaultItemCreate,
    user = Depends(get_current_user),
):
    repo = pick_repo()
    ct = encrypt(payload.secret)
    item = repo.create_item(user_id=user["id"], title=payload.title, ciphertext=ct)
    return VaultItemOut.from_orm(item)

@router.get("/", response_model=List[VaultItemOut])
def list_vault_items(user = Depends(get_current_user)):
    repo = pick_repo()
    items = repo.list_items(user_id=user["id"])
    return [VaultItemOut.from_orm(i) for i in items]

@router.get("/{item_id}", response_model=VaultItemDetail)
def read_vault_item(item_id: str, user = Depends(get_current_user)):
    repo = pick_repo()
    item = repo.get_item(user_id=user["id"], item_id=item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return VaultItemDetail(
        id=item.id,
        title=item.title,
        secret=decrypt(item.data),
        created_at=item.created_at,
    )