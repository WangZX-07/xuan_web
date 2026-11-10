from __future__ import annotations

import pytest
from sqlalchemy import update
from sqlalchemy.exc import DatabaseError

from app.core.security import hash_token
from app.models.entities import AuditEvent


def test_secret_hash_is_deterministic_and_not_plaintext():
    value = "a-sensitive-session-token"
    assert hash_token(value) == hash_token(value)
    assert hash_token(value) != value
    assert len(hash_token(value)) == 64


def test_audit_table_is_append_only(db):
    event = AuditEvent(action="content.publish", entity_type="content_version")
    db.add(event)
    db.commit()
    with pytest.raises(DatabaseError):
        db.execute(update(AuditEvent).where(AuditEvent.id == event.id).values(action="tampered"))
        db.commit()
    db.rollback()
