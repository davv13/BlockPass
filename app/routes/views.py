# app/routes/views.py
from fastapi import APIRouter, Request, Form, Depends, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.repository import pick_repo
from app.core.auth import get_current_user
from app.core.security import verify_password, create_access_token, hash_password
from app.core.config import get_settings
from app.core import kdf, encryption           # ← NEW: AES‑256‑GCM helpers

templates = Jinja2Templates(directory="templates")
router = APIRouter()
settings = get_settings()

# ── REGISTER ───────────────────────────────────────────────────────────
@router.get("/register", response_class=HTMLResponse)
def reg_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
def reg_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    repo = pick_repo()
    try:
        # create_user() now auto‑generates kdf_salt when omitted
        repo.create_user(username, hash_password(password))
    except ValueError:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already exists"},
        )
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

# ── LOGIN ──────────────────────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    repo = pick_repo()
    user = repo.get_by_username(username)
    if not user or not verify_password(password, user["password"]):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
        )
    token = create_access_token({"sub": user["id"]})
    resp = RedirectResponse("/vault", status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie("access_token", token, httponly=True)
    return resp

# ── LOGOUT ─────────────────────────────────────────────────────────────
@router.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    resp.delete_cookie("access_token")
    return resp

# ── VAULT LIST ─────────────────────────────────────────────────────────
@router.get("/vault", response_class=HTMLResponse)
def vault_list(request: Request, user=Depends(get_current_user)):
    items = pick_repo().list_items(user_id=user["id"])
    return templates.TemplateResponse(
        "vault_list.html",
        {"request": request, "items": items},
    )

# ── VAULT CREATE ───────────────────────────────────────────────────────
@router.get("/vault/create", response_class=HTMLResponse)
def vault_create_form(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("vault_create.html", {"request": request})

@router.post("/vault/create", response_class=HTMLResponse)
def vault_create(
    request: Request,
    title: str = Form(...),
    secret: str = Form(...),
    master_password: str = Form(...),          # ← NEW field in the form
    user=Depends(get_current_user),
):
    repo = pick_repo()

    # derive per‑user key
    key = kdf.derive_key(
        master_password,
        salt=bytes.fromhex(user["kdf_salt"]),
        mem_kib=user["kdf_mem"],
        time=user["kdf_time"],
        lanes=user["kdf_lanes"],
    )

    try:
        blob = encryption.encrypt(secret, key)
    finally:
        del key                                  # secure‑wipe

    repo.create_item(user_id=user["id"], title=title, ciphertext=blob)
    return RedirectResponse("/vault", status_code=status.HTTP_303_SEE_OTHER)

# ── VAULT DETAIL ───────────────────────────────────────────────────────
@router.get("/vault/{item_id}", response_class=HTMLResponse)
def vault_detail(
    request: Request,
    item_id: str,
    user=Depends(get_current_user),
):
    repo = pick_repo()
    item = repo.get_item(user_id=user["id"], item_id=item_id)
    if not item:
        return RedirectResponse("/vault", status_code=status.HTTP_303_SEE_OTHER)
    # show a small form asking for the master password
    return templates.TemplateResponse(
        "vault_detail.html",
        {"request": request, "item": item, "secret": None},
    )

@router.post("/vault/{item_id}", response_class=HTMLResponse)
def vault_reveal(
    request: Request,
    item_id: str,
    master_password: str = Form(...),
    user=Depends(get_current_user),
):
    repo = pick_repo()
    item = repo.get_item(user_id=user["id"], item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    key = kdf.derive_key(
        master_password,
        salt=bytes.fromhex(user["kdf_salt"]),
        mem_kib=user["kdf_mem"],
        time=user["kdf_time"],
        lanes=user["kdf_lanes"],
    )

    try:
        plaintext = encryption.decrypt(item.data, key)
    except Exception:
        plaintext = "*** decryption failed ***"
    finally:
        del key

    return templates.TemplateResponse(
        "vault_detail.html",
        {"request": request, "item": item, "secret": plaintext},
    )

# ── VAULT DELETE ───────────────────────────────────────────────────────
@router.post("/vault/{item_id}/delete")
def vault_delete(item_id: str, user=Depends(get_current_user)):
    repo = pick_repo()
    repo.delete_item(user_id=user["id"], item_id=item_id)
    return RedirectResponse("/vault", status_code=303)