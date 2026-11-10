from __future__ import annotations

import hmac
import json
from datetime import timedelta
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    EditorAdmin,
    get_current_admin,
    hash_token,
    is_expired,
    random_token,
    utc_now,
)
from app.models.entities import AdminIdentity, AdminRole, AdminSession, OAuthState
from app.services.audit import write_audit
from app.services.feishu import FeishuClient


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/feishu/start")
def start_feishu_login(db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.feishu_configured:
        raise HTTPException(status_code=503, detail="飞书登录尚未完成服务器配置")
    raw_state = random_token()
    db.add(
        OAuthState(
            state_hash=hash_token(raw_state),
            expires_at=utc_now() + timedelta(minutes=10),
        )
    )
    db.commit()
    response = RedirectResponse(FeishuClient(settings).authorize_url(raw_state), status_code=302)
    response.set_cookie(
        settings.oauth_cookie_name,
        raw_state,
        max_age=600,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/auth/feishu/callback",
    )
    return response


@router.get("/feishu/callback")
async def feishu_callback(
    request: Request,
    code: str = Query(min_length=2),
    state_value: str = Query(alias="state", min_length=16),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    state_cookie = request.cookies.get(settings.oauth_cookie_name, "")
    if not state_cookie or not hmac.compare_digest(state_cookie, state_value):
        raise HTTPException(status_code=403, detail="OAuth state 校验失败")
    record = db.scalar(select(OAuthState).where(OAuthState.state_hash == hash_token(state_value)))
    if record is None or record.used_at is not None or is_expired(record.expires_at):
        raise HTTPException(status_code=403, detail="OAuth state 已失效或已使用")
    record.used_at = utc_now()
    db.commit()

    client = FeishuClient(settings)
    access_token = await client.exchange_code(code)
    user = await client.fetch_user(access_token)
    client.ensure_allowed(user)

    identity = db.scalar(select(AdminIdentity).where(AdminIdentity.open_id == user.open_id))
    role = AdminRole.owner.value if user.open_id in settings.feishu_owner_open_ids else AdminRole.editor.value
    if identity is None:
        identity = AdminIdentity(
            open_id=user.open_id,
            tenant_key=user.tenant_key,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            department_ids_json=json.dumps(user.department_ids),
            role=role,
        )
        db.add(identity)
        db.flush()
    else:
        identity.tenant_key = user.tenant_key
        identity.display_name = user.display_name
        identity.avatar_url = user.avatar_url
        identity.department_ids_json = json.dumps(user.department_ids)
        if user.open_id in settings.feishu_owner_open_ids:
            identity.role = AdminRole.owner.value
    identity.last_login_at = utc_now()
    session_token = random_token()
    csrf_token = random_token()
    session = AdminSession(
        identity_id=identity.id,
        token_hash=hash_token(session_token),
        csrf_hash=hash_token(csrf_token),
        expires_at=utc_now() + timedelta(hours=settings.session_ttl_hours),
    )
    db.add(session)
    write_audit(db, request, None, "auth.login", "admin_identity", identity.id)
    db.commit()

    response = RedirectResponse(f"{settings.admin_origin}/?login=success", status_code=302)
    max_age = settings.session_ttl_hours * 3600
    response.set_cookie(
        settings.session_cookie_name,
        session_token,
        max_age=max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="strict",
        path="/",
    )
    response.delete_cookie(settings.oauth_cookie_name, path="/auth/feishu/callback")
    return response


@router.post("/logout")
def logout(request: Request, admin: EditorAdmin, db: Session = Depends(get_db)):
    settings = get_settings()
    write_audit(db, request, admin, "auth.logout", "admin_session", admin.session.id)
    db.delete(admin.session)
    db.commit()
    response = RedirectResponse(f"{settings.admin_origin}/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")
    return response


@router.get("/session")
def session_info(request: Request, admin=Depends(get_current_admin)):
    settings = get_settings()
    csrf = request.cookies.get(settings.csrf_cookie_name, "")
    return {
        "id": admin.identity.id,
        "display_name": admin.identity.display_name,
        "avatar_url": admin.identity.avatar_url,
        "role": admin.identity.role,
        "expires_at": admin.session.expires_at,
        "csrf_token": csrf,
    }
