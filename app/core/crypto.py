# app/core/crypto.py
"""
DEPRECATED shim.
Funnel all legacy imports to the new AES‑256‑GCM implementation.
Remove this file once every module imports `app.core.encryption` directly.
"""
from app.core.encryption import encrypt, decrypt  # noqa: F401
