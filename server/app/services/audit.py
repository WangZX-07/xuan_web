from __future__ import annotations

import json

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.security import CurrentAdmin, hash_ip
from app.models.entities import AuditEvent


def write_audit(
    db: Session,
    request: Request,
    admin: CurrentAdmin | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    payload: dict | None = None,
) -> AuditEvent:
    forwarded = request.headers.get("x-forwarded-for", "")
    raw_ip = forwarded.split(",", 1)[0].strip() or (request.client.host if request.client else None)
    event = AuditEvent(
        actor_id=admin.identity.id if admin else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload_json=json.dumps(payload or {}, ensure_ascii=False, separators=(",", ":")),
        ip_hash=hash_ip(raw_ip),
    )
    db.add(event)
    return event
