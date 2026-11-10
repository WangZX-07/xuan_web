from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class AdminRole(str, enum.Enum):
    editor = "editor"
    publisher = "publisher"
    owner = "owner"


class ReleaseStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class UploadStatus(str, enum.Enum):
    initialized = "initialized"
    uploading = "uploading"
    verifying = "verifying"
    scanning = "scanning"
    ready = "ready"
    failed = "failed"
    cancelled = "cancelled"
    published = "published"


class AssetStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


class AdminIdentity(Base):
    __tablename__ = "admin_identities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    open_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    tenant_key: Mapped[str] = mapped_column(String(128), index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    avatar_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    department_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    role: Mapped[str] = mapped_column(String(24), default=AdminRole.editor.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list["AdminSession"]] = relationship(
        back_populates="identity", cascade="all, delete-orphan"
    )


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    identity_id: Mapped[str] = mapped_column(ForeignKey("admin_identities.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    identity: Mapped[AdminIdentity] = relationship(back_populates="sessions")


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    state_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SiteDraft(Base):
    __tablename__ = "site_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    content_json: Mapped[str] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[str | None] = mapped_column(
        ForeignKey("admin_identities.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ContentVersion(Base):
    __tablename__ = "content_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    version_number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    content_json: Mapped[str] = mapped_column(Text)
    release_note: Mapped[str] = mapped_column(String(500))
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("admin_identities.id", ondelete="SET NULL"), nullable=True
    )
    rolled_back_from_id: Mapped[str | None] = mapped_column(
        ForeignKey("content_versions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    original_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(80))
    byte_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    original_path: Mapped[str] = mapped_column(String(1000))
    optimized_path: Mapped[str] = mapped_column(String(1000))
    alt_text: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(24), default=AssetStatus.active.value)
    uploaded_by: Mapped[str | None] = mapped_column(
        ForeignKey("admin_identities.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class UploadJob(Base):
    __tablename__ = "upload_jobs"
    __table_args__ = (
        Index("ix_upload_jobs_status_updated", "status", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    version: Mapped[str] = mapped_column(String(64))
    channel: Mapped[str] = mapped_column(String(64))
    platform: Mapped[str] = mapped_column(String(80))
    release_notes: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(String(255))
    total_size: Mapped[int] = mapped_column(Integer)
    chunk_size: Mapped[int] = mapped_column(Integer)
    expected_chunks: Mapped[int] = mapped_column(Integer)
    received_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default=UploadStatus.initialized.value)
    temp_path: Mapped[str] = mapped_column(String(1000))
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    bytes_per_second: Mapped[float] = mapped_column(Float, default=0.0)
    eta_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("admin_identities.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    chunks: Mapped[list["UploadChunk"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    events: Mapped[list["JobEvent"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class UploadChunk(Base):
    __tablename__ = "upload_chunks"
    __table_args__ = (
        UniqueConstraint("job_id", "chunk_index", name="uq_upload_chunk_index"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("upload_jobs.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    offset: Mapped[int] = mapped_column(Integer)
    byte_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    job: Mapped[UploadJob] = relationship(back_populates="chunks")


class JobEvent(Base):
    __tablename__ = "job_events"
    __table_args__ = (
        Index("ix_job_events_job_id_id", "job_id", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("upload_jobs.id", ondelete="CASCADE"))
    phase: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(String(500))
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    job: Mapped[UploadJob] = relationship(back_populates="events")


class Release(Base):
    __tablename__ = "releases"
    __table_args__ = (
        UniqueConstraint("version", "channel", "platform", name="uq_release_version_channel_platform"),
        Index("ix_releases_current_status", "is_current", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    version: Mapped[str] = mapped_column(String(64))
    channel: Mapped[str] = mapped_column(String(64))
    platform: Mapped[str] = mapped_column(String(80))
    release_notes: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1000))
    byte_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default=ReleaseStatus.draft.value)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_by: Mapped[str | None] = mapped_column(
        ForeignKey("admin_identities.id", ondelete="SET NULL"), nullable=True
    )
    published_by: Mapped[str | None] = mapped_column(
        ForeignKey("admin_identities.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DownloadDaily(Base):
    __tablename__ = "download_daily"
    __table_args__ = (
        UniqueConstraint("release_id", "day", name="uq_download_release_day"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    release_id: Mapped[str] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"))
    day: Mapped[date] = mapped_column(Date, default=date.today)
    started_count: Mapped[int] = mapped_column(Integer, default=0)
    requested_bytes: Mapped[int] = mapped_column(Integer, default=0)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_created_id", "created_at", "id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_id: Mapped[str | None] = mapped_column(
        ForeignKey("admin_identities.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
