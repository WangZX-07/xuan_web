from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.-]+)?$")


class UploadInitializeRequest(BaseModel):
    version: str = Field(max_length=64)
    channel: str = Field(default="preview", min_length=2, max_length=64)
    platform: str = Field(default="Windows x64", min_length=2, max_length=80)
    release_notes: str = Field(min_length=2, max_length=5000)
    file_name: str = Field(min_length=3, max_length=255)
    total_size: int = Field(gt=0)

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        value = value.strip().lower().lstrip("v")
        if not VERSION_RE.fullmatch(value):
            raise ValueError("版本号需符合 SemVer，例如 0.3.0-beta.1")
        return value

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, value: str) -> str:
        if any(part in value for part in ("/", "\\", "..")):
            raise ValueError("文件名不合法")
        if not value.lower().endswith((".exe", ".msi")):
            raise ValueError("仅支持 Windows EXE 或 MSI 安装包")
        return value


class UploadJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: str
    channel: str
    platform: str
    file_name: str
    total_size: int
    chunk_size: int
    expected_chunks: int
    received_bytes: int
    status: str
    progress: float
    bytes_per_second: float
    eta_seconds: int | None
    sha256: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ReleaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: str
    channel: str
    platform: str
    release_notes: str
    file_name: str
    byte_size: int
    sha256: str
    status: str
    is_current: bool
    created_at: datetime
    published_at: datetime | None


class PublishRequest(BaseModel):
    make_current: bool = True


class DeleteReleaseRequest(BaseModel):
    confirmation: str
