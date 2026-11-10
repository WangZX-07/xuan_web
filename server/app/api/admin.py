from __future__ import annotations

import json
import shutil

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import EditorAdmin, OwnerAdmin
from app.models.entities import (
    AdminIdentity,
    AuditEvent,
    ContentVersion,
    DownloadDaily,
    Release,
    ReleaseStatus,
    SiteDraft,
    UploadJob,
)
from app.schemas.auth import RoleUpdateRequest
from app.services.audit import write_audit


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(admin: EditorAdmin, db: Session = Depends(get_db)):
    settings = get_settings()
    current = db.scalar(select(Release).where(Release.is_current.is_(True)))
    preview = db.scalar(
        select(Release)
        .where(Release.status == ReleaseStatus.draft.value)
        .order_by(Release.created_at.desc())
    )
    draft = db.get(SiteDraft, 1)
    published = db.scalar(select(ContentVersion).order_by(ContentVersion.version_number.desc()))
    jobs = db.scalars(
        select(UploadJob).order_by(UploadJob.updated_at.desc()).limit(6)
    ).all()
    downloads = db.scalar(select(func.sum(DownloadDaily.started_count))) or 0
    disk = shutil.disk_usage(settings.data_dir)
    backup_files = list(settings.backup_dir.glob("*"))
    return {
        "current_release": (
            {"id": current.id, "version": current.version, "platform": current.platform}
            if current
            else None
        ),
        "preview_release": (
            {"id": preview.id, "version": preview.version, "platform": preview.platform}
            if preview
            else None
        ),
        "cms_dirty": bool(draft and published and draft.content_json != published.content_json),
        "content_version": published.version_number if published else None,
        "download_starts": downloads,
        "jobs": [
            {
                "id": item.id,
                "version": item.version,
                "status": item.status,
                "progress": item.progress,
                "updated_at": item.updated_at,
            }
            for item in jobs
        ],
        "disk": {"free": disk.free, "total": disk.total, "used": disk.used},
        "backup": {
            "status": "ok" if backup_files else "pending",
            "last_file": max((item.name for item in backup_files), default=None),
        },
        "services": {"api": "healthy", "database": "healthy"},
    }


@router.get("/download-trends")
def download_trends(admin: EditorAdmin, db: Session = Depends(get_db)):
    rows = db.execute(
        select(DownloadDaily.day, func.sum(DownloadDaily.started_count))
        .group_by(DownloadDaily.day)
        .order_by(DownloadDaily.day.desc())
        .limit(30)
    ).all()
    return [{"day": day, "count": count} for day, count in reversed(rows)]


@router.get("/audit-events")
def audit_events(
    admin: EditorAdmin,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count(AuditEvent.id))) or 0
    items = db.scalars(
        select(AuditEvent)
        .order_by(AuditEvent.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "total": total,
        "page": page,
        "items": [
            {
                "id": item.id,
                "actor_id": item.actor_id,
                "action": item.action,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "payload": json.loads(item.payload_json),
                "created_at": item.created_at,
            }
            for item in items
        ],
    }


@router.get("/identities")
def list_identities(admin: OwnerAdmin, db: Session = Depends(get_db)):
    identities = db.scalars(select(AdminIdentity).order_by(AdminIdentity.created_at.asc())).all()
    return [
        {
            "id": item.id,
            "display_name": item.display_name,
            "role": item.role,
            "is_active": item.is_active,
            "last_login_at": item.last_login_at,
        }
        for item in identities
    ]


@router.put("/identities/{identity_id}/role")
def update_identity_role(
    identity_id: str,
    payload: RoleUpdateRequest,
    request: Request,
    admin: OwnerAdmin,
    db: Session = Depends(get_db),
):
    identity = db.get(AdminIdentity, identity_id)
    if identity is None:
        raise HTTPException(status_code=404, detail="成员不存在")
    if identity.id == admin.identity.id and payload.role != "owner":
        raise HTTPException(status_code=409, detail="不能移除自己的所有者权限")
    old = identity.role
    identity.role = payload.role
    write_audit(
        db,
        request,
        admin,
        "identity.role.update",
        "admin_identity",
        identity.id,
        {"from": old, "to": payload.role},
    )
    db.commit()
    return {"ok": True}
