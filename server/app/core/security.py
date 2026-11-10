from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.entities import AdminIdentity, AdminRole, AdminSession


ROLE_LEVEL = {
    AdminRole.editor.value: 10,
    AdminRole.publisher.value: 20,
    AdminRole.owner.value: 30,
}


def random_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_ip(value: str | None) -> str | None:
    if not value:
        return None
    salt = get_settings().ip_hash_salt or "local-development-only"
    return hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_expired(value: datetime) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= utc_now()


@dataclass(slots=True)
class CurrentAdmin:
    identity: AdminIdentity
    session: AdminSession


def get_current_admin(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> CurrentAdmin:
    settings = get_settings()
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    session = db.scalar(
        select(AdminSession).where(AdminSession.token_hash == hash_token(raw_token))
    )
    if session is None or is_expired(session.expires_at):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="会话已过期")
    identity = db.get(AdminIdentity, session.identity_id)
    if identity is None or not identity.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号不可用")
    session.last_seen_at = utc_now()
    db.commit()
    return CurrentAdmin(identity=identity, session=session)


def require_role(minimum: AdminRole) -> Callable:
    def dependency(
        request: Request,
        admin: Annotated[CurrentAdmin, Depends(get_current_admin)],
    ) -> CurrentAdmin:
        if ROLE_LEVEL.get(admin.identity.role, 0) < ROLE_LEVEL[minimum.value]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            settings = get_settings()
            presented = request.headers.get(settings.csrf_header_name, "")
            cookie = request.cookies.get(settings.csrf_cookie_name, "")
            if not presented or not cookie or not hmac.compare_digest(presented, cookie):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF 校验失败")
            if not hmac.compare_digest(hash_token(presented), admin.session.csrf_hash):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF 校验失败")
        return admin

    return dependency


EditorAdmin = Annotated[CurrentAdmin, Depends(require_role(AdminRole.editor))]
PublisherAdmin = Annotated[CurrentAdmin, Depends(require_role(AdminRole.publisher))]
OwnerAdmin = Annotated[CurrentAdmin, Depends(require_role(AdminRole.owner))]
