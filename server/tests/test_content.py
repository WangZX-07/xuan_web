from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.entities import ContentVersion
from sqlalchemy import update
from sqlalchemy.exc import DatabaseError
from app.schemas.content import PublishedSiteContent, default_site_content
from app.services.content import ensure_initial_content, get_draft, get_published, validation_checks


def test_default_content_is_publishable_and_has_required_boundaries():
    content = default_site_content()
    checks = validation_checks(content)
    assert not [item for item in checks if item["level"] == "error"]
    assert "不得直接用于患者治疗决策" in content.safety.statements
    assert {item.status for item in content.progress} == {"implemented", "researching", "pending"}


def test_script_payload_is_rejected():
    payload = default_site_content().model_dump()
    payload["hero"]["description"] = "<script>alert(1)</script>" + ("x" * 20)
    with pytest.raises(ValidationError):
        PublishedSiteContent.model_validate(payload)


def test_initial_content_creates_draft_and_immutable_version(db):
    ensure_initial_content(db)
    draft, draft_content = get_draft(db)
    published, published_content = get_published(db)
    assert draft.revision == 1
    assert published.version_number == 1
    assert draft_content.hero.title == published_content.hero.title
    assert db.query(ContentVersion).count() == 1
    with pytest.raises(DatabaseError):
        db.execute(
            update(ContentVersion)
            .where(ContentVersion.id == published.id)
            .values(release_note="tampered")
        )
        db.commit()
    db.rollback()
