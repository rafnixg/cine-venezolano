from __future__ import annotations

import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import HTTPException, Request, status

from app.config import settings

hasher = PasswordHasher()


def verify_admin_password(password: str) -> bool:
    if not settings.admin_password_hash:
        return False
    try:
        return hasher.verify(settings.admin_password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def require_admin(request: Request) -> None:
    if not request.session.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/admin/login"}
        )


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def validate_csrf(request: Request, submitted: str) -> None:
    expected = request.session.get("csrf_token", "")
    if not expected or not hmac.compare_digest(expected, submitted):
        raise HTTPException(status_code=403, detail="Token CSRF inválido")
