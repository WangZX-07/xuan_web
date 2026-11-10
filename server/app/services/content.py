from __future__ import annotations

import json

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import ContentVersion, SiteDraft
from app.schemas.content import PublishedSiteContent, default_site_content


def serialize_content(content: PublishedSiteContent) -> str:
    return content.model_dump_json()


def parse_content(raw: str) -> PublishedSiteContent:
    try:
        return PublishedSiteContent.model_validate_json(raw)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=json.loads(exc.json())) from exc


def ensure_initial_content(db: Session) -> None:
    default = default_site_content()
    draft = db.get(SiteDraft, 1)
    if draft is None:
        db.add(SiteDraft(id=1, content_json=serialize_content(default), revision=1))
    exists = db.scalar(select(func.count(ContentVersion.id))) or 0
    if exists == 0:
        db.add(
            ContentVersion(
                version_number=1,
                content_json=serialize_content(default),
                release_note="系统初始化内容",
            )
        )
    db.commit()


def get_draft(db: Session) -> tuple[SiteDraft, PublishedSiteContent]:
    draft = db.get(SiteDraft, 1)
    if draft is None:
        ensure_initial_content(db)
        draft = db.get(SiteDraft, 1)
    assert draft is not None
    return draft, parse_content(draft.content_json)


def get_published(db: Session) -> tuple[ContentVersion, PublishedSiteContent]:
    version = db.scalar(select(ContentVersion).order_by(ContentVersion.version_number.desc()))
    if version is None:
        ensure_initial_content(db)
        version = db.scalar(select(ContentVersion).order_by(ContentVersion.version_number.desc()))
    assert version is not None
    return version, parse_content(version.content_json)


def validation_checks(content: PublishedSiteContent) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    for item in content.safety.statements:
        checks.append({"level": "pass", "message": f"安全声明已包含：{item}"})
    for field, alt in (("hero", content.hero.image_alt), ("tici", content.tici.image_alt)):
        checks.append(
            {
                "level": "pass" if len(alt) >= 6 else "error",
                "message": f"{field} 图片替代文本已填写" if len(alt) >= 6 else f"{field} 缺少图片替代文本",
            }
        )
    suspicious = ["准确率", "敏感度", "特异度", "%", "临床验证", "疗效提升"]
    body = content.model_dump_json()
    for word in suspicious:
        if word in body:
            checks.append({"level": "warning", "message": f"发现需人工核验的表述：{word}"})
    return checks
