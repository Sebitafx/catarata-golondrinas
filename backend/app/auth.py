import os
import secrets
from fastapi import Header, HTTPException


def require_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")):
    expected = os.getenv("ADMIN_KEY", "test-admin-key")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=401, detail="no autorizado")
    return True
