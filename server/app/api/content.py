from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import EditorAdmin, PublisherAdmin
from app.models.entities import ContentVersion
from app.schemas.content import PublishedSiteContent
from app.services.audit import write_audit
from app.services.content import (
    get_draft,
    parse_content,
    serialize_content,
    validation_checks,
)


router = APIRouter(prefix="/api/admin/content", tags=["admin-content"])


class DraftUpdate(BaseModel):
    revision: int = Field(ge=1)
    content: PublishedSiteContent


class PublishContentRequest(BaseModel):
    release_note: str = Field(min_length=2, max_length=500)


@router.get("/draft")
def read_draft(admin: EditorAdmin, db: Session = Depends(get_db)):
    draft, content = get_draft(db)
    return {"revision": draft.revision, "updated_at": draft.updated_at, "content": content}


@router.put("/draft")
def update_draft(
    payload: DraftUpdate,
    request: Request,
    admin: EditorAdmin,
    db: Session = Depends(get_db),
):
    draft, _ = get_draft(db)
    if payload.revision != draft.revision:
        raise HTTPException(status_code=409, detail="草稿已被其他编辑更新，请刷新后重试")
    draft.content_json = serialize_content(payload.content)
    draft.revision += 1
    draft.updated_by = admin.identity.id
    checks = validation_checks(payload.content)
    write_audit(
        db, request, admin, "content.draft.update", "site_draft", str(draft.id), {"revision": draft.revision}
    )
    db.commit()
    return {"revision": draft.revision, "updated_at": draft.updated_at, "checks": checks}


@router.get("/validation")
def validate_draft(admin: EditorAdmin, db: Session = Depends(get_db)):
    _, content = get_draft(db)
    checks = validation_checks(content)
    return {"can_publish": not any(item["level"] == "error" for item in checks), "checks": checks}


@router.post("/publish")
def publish_content(
    payload: PublishContentRequest,
    request: Request,
    admin: PublisherAdmin,
    db: Session = Depends(get_db),
):
    draft, content = get_draft(db)
    checks = validation_checks(content)
    if any(item["level"] == "error" for item in checks):
        raise HTTPException(status_code=422, detail=checks)
    next_number = (db.scalar(select(func.max(ContentVersion.version_number))) or 0) + 1
    version = ContentVersion(
        version_number=next_number,
        content_json=draft.content_json,
        release_note=payload.release_note,
        created_by=admin.identity.id,
    )
    db.add(version)
    write_audit(
        db, request, admin, "content.publish", "content_version", None, {"version": next_number}
    )
    db.commit()
    db.refresh(version)
    return {"id": version.id, "version_number": version.version_number, "created_at": version.created_at}


@router.get("/versions")
def list_versions(admin: EditorAdmin, db: Session = Depends(get_db)):
    versions = db.scalars(
        select(ContentVersion).order_by(ContentVersion.version_number.desc()).limit(100)
    ).all()
    return [
        {
            "id": item.id,
            "version_number": item.version_number,
            "release_note": item.release_note,
            "created_by": item.created_by,
            "rolled_back_from_id": item.rolled_back_from_id,
            "created_at": item.created_at,
        }
        for item in versions
    ]


@router.get("/versions/{version_id}")
def read_version(version_id: str, admin: EditorAdmin, db: Session = Depends(get_db)):
    version = db.get(ContentVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="内容版本不存在")
    return {
        "id": version.id,
        "version_number": version.version_number,
        "release_note": version.release_note,
        "created_at": version.created_at,
        "content": parse_content(version.content_json),
    }


@router.post("/versions/{version_id}/rollback")
def rollback_content(
    version_id: str,
    payload: PublishContentRequest,
    request: Request,
    admin: PublisherAdmin,
    db: Session = Depends(get_db),
):
    source = db.get(ContentVersion, version_id)
    if source is None:
        raise HTTPException(status_code=404, detail="内容版本不存在")
    next_number = (db.scalar(select(func.max(ContentVersion.version_number))) or 0) + 1
    restored = ContentVersion(
        version_number=next_number,
        content_json=source.content_json,
        release_note=payload.release_note,
        created_by=admin.identity.id,
        rolled_back_from_id=source.id,
    )
    draft, _ = get_draft(db)
    draft.content_json = source.content_json
    draft.revision += 1
    draft.updated_by = admin.identity.id
    db.add(restored)
    write_audit(
        db,
        request,
        admin,
        "content.rollback",
        "content_version",
        source.id,
        {"new_version": next_number},
    )
    db.commit()
    db.refresh(restored)
    return {"id": restored.id, "version_number": restored.version_number}
