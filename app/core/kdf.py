"""
kdf.py – Argon2id helpers for per‑user vault keys
Requires `argon2‑cffi` 23.1.0+  (pip install argon2‑cffi)
"""

import secrets
from typing import Tuple

from argon2.low_level import hash_secret_raw, Type


# --------------------------- configuration defaults ---------------------------

# 19 MiB of RAM (kibibytes) and two passes ≈ 200–300 ms on a modern desktop.
DEFAULT_MEM_KIB = 19 * 1024
DEFAULT_TIME    = 2
DEFAULT_LANES   = 1           # single‑thread (set >1 on servers with many cores)


# --------------------------------- helpers ------------------------------------

def generate_salt(length: int = 16) -> bytes:
    """Return a cryptographically‑random salt (default 128 bits)."""
    return secrets.token_bytes(length)


def derive_key(
    master_pwd: str,
    salt: bytes,
    *,
    mem_kib: int = DEFAULT_MEM_KIB,
    time: int    = DEFAULT_TIME,
    lanes: int   = DEFAULT_LANES,
) -> bytes:
    """
    Derive a 256‑bit key from `master_pwd` and `salt` using Argon2id.
    All parameters are expressed in Argon2's native units:
      • mem_kib – kibibytes of RAM to use
      • time    – number of iterations (passes)
      • lanes   – degree of parallelism
    """
    if not master_pwd:
        raise ValueError("master_pwd must be non‑empty")

    return hash_secret_raw(
        secret      = master_pwd.encode("utf‑8"),
        salt        = salt,
        time_cost   = time,
        memory_cost = mem_kib,
        parallelism = lanes,
        hash_len    = 32,         # 256‑bit key
        type        = Type.ID,    # Argon2id variant
    )


def default_kdf_params() -> Tuple[int, int, int]:
    """Expose defaults so callers can persist them next to the salt."""
    return DEFAULT_MEM_KIB, DEFAULT_TIME, DEFAULT_LANES