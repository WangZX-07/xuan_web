from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.models.entities import UploadJob
from app.schemas.release import UploadInitializeRequest
from app.services.uploads import _verify_header, initialize_upload, save_chunk


def configure_paths(tmp_path):
    settings = get_settings()
    settings.data_dir = tmp_path
    settings.upload_dir = tmp_path / "uploads"
    settings.release_dir = tmp_path / "releases"
    settings.asset_dir = tmp_path / "assets"
    settings.backup_dir = tmp_path / "backups"
    settings.minimum_free_bytes = 0
    settings.upload_chunk_size = 4
    settings.upload_max_bytes = 1024
    for path in (settings.upload_dir, settings.release_dir, settings.asset_dir, settings.backup_dir):
        path.mkdir(exist_ok=True)


def test_chunk_hash_is_verified_and_resume_is_idempotent(db, tmp_path):
    configure_paths(tmp_path)
    payload = UploadInitializeRequest(
        version="0.3.0",
        channel="preview",
        platform="Windows x64",
        release_notes="测试上传",
        file_name="LungTic.exe",
        total_size=8,
    )
    job = initialize_upload(db, payload, "actor")
    chunk = b"MZ12"
    digest = hashlib.sha256(chunk).hexdigest()
    updated = save_chunk(db, job, 0, chunk, digest)
    assert updated.received_bytes == 4
    resumed = save_chunk(db, job, 0, chunk, digest)
    assert resumed.received_bytes == 4
    with pytest.raises(HTTPException) as caught:
        save_chunk(db, job, 1, b"BAD!", "0" * 64)
    assert caught.value.status_code == 422


def test_pe_headers_are_checked(tmp_path):
    executable = tmp_path / "ok.exe"
    executable.write_bytes(b"MZ" + b"\0" * 10)
    _verify_header(executable, executable.name)
    broken = tmp_path / "bad.exe"
    broken.write_bytes(b"NOPE")
    with pytest.raises(ValueError):
        _verify_header(broken, broken.name)
