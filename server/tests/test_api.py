from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_token, utc_now
from app.main import app
from app.models.entities import AdminIdentity, AdminSession
from app.services.content import ensure_initial_content
from app.api.public import requested_size


@pytest.fixture()
def client(db):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def sign_in(db, client: TestClient, role: str):
    raw_session = "session-" + role
    raw_csrf = "csrf-" + role
    identity = AdminIdentity(
        open_id="open-" + role,
        tenant_key="tenant",
        display_name=role,
        role=role,
    )
    db.add(identity)
    db.flush()
    db.add(
        AdminSession(
            identity_id=identity.id,
            token_hash=hash_token(raw_session),
            csrf_hash=hash_token(raw_csrf),
            expires_at=utc_now() + timedelta(hours=1),
        )
    )
    db.commit()
    settings = get_settings()
    client.cookies.set(settings.session_cookie_name, raw_session)
    client.cookies.set(settings.csrf_cookie_name, raw_csrf)
    return {settings.csrf_header_name: raw_csrf}


def test_public_site_returns_published_snapshot(client, db):
    ensure_initial_content(db)
    response = client.get("/api/public/site")
    assert response.status_code == 200
    payload = response.json()
    assert payload["content_version"] == 1
    assert payload["content"]["hero"]["title"] == "让呼吸运动不再成为精准放疗的盲区"


def test_editor_cannot_publish(client, db):
    ensure_initial_content(db)
    headers = sign_in(db, client, "editor")
    response = client.post(
        "/api/admin/content/publish",
        headers=headers,
        json={"release_note": "不应发布"},
    )
    assert response.status_code == 403


def test_publisher_needs_csrf_and_can_publish(client, db):
    ensure_initial_content(db)
    headers = sign_in(db, client, "publisher")
    missing = client.post(
        "/api/admin/content/publish",
        json={"release_note": "缺少 CSRF"},
    )
    assert missing.status_code == 403
    published = client.post(
        "/api/admin/content/publish",
        headers=headers,
        json={"release_note": "通过测试发布"},
    )
    assert published.status_code == 200
    assert published.json()["version_number"] == 2


def test_range_size_is_aggregated_without_storing_requester_ip():
    assert requested_size(None, 1000) == 1000
    assert requested_size("bytes=100-199", 1000) == 100
    assert requested_size("bytes=900-", 1000) == 100
    assert requested_size("bytes=-50", 1000) == 50
    assert requested_size("not-a-range", 1000) == 1000
