from __future__ import annotations

import hashlib
import math
import os
import shutil
import time
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.entities import (
    JobEvent,
    Release,
    UploadChunk,
    UploadJob,
    UploadStatus,
    utc_now,
)
from app.schemas.release import UploadInitializeRequest
from app.services.clamav import MalwareScanError, scan_file


def add_event(db: Session, job: UploadJob, phase: str, message: str, progress: float) -> None:
    job.status = phase
    job.progress = max(0.0, min(progress, 100.0))
    job.updated_at = utc_now()
    db.add(JobEvent(job_id=job.id, phase=phase, message=message, progress=job.progress))
    db.commit()


def initialize_upload(db: Session, data: UploadInitializeRequest, actor_id: str) -> UploadJob:
    settings = get_settings()
    if data.total_size > settings.upload_max_bytes:
        raise HTTPException(status_code=413, detail="安装包超过允许大小")
    free = shutil.disk_usage(settings.upload_dir).free
    if free - data.total_size < settings.minimum_free_bytes:
        raise HTTPException(status_code=507, detail="服务器磁盘空间不足")
    duplicate = db.scalar(
        select(Release).where(
            Release.version == data.version,
            Release.channel == data.channel,
            Release.platform == data.platform,
        )
    )
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="该版本、渠道和平台已存在")
    active = db.scalar(
        select(UploadJob).where(
            UploadJob.version == data.version,
            UploadJob.channel == data.channel,
            UploadJob.platform == data.platform,
            UploadJob.status.notin_(
                [UploadStatus.failed.value, UploadStatus.cancelled.value, UploadStatus.published.value]
            ),
        )
    )
    if active is not None:
        return active
    chunk_size = settings.upload_chunk_size
    job = UploadJob(
        version=data.version,
        channel=data.channel,
        platform=data.platform,
        release_notes=data.release_notes,
        file_name=data.file_name,
        total_size=data.total_size,
        chunk_size=chunk_size,
        expected_chunks=math.ceil(data.total_size / chunk_size),
        status=UploadStatus.initialized.value,
        temp_path="pending",
        created_by=actor_id,
    )
    db.add(job)
    db.flush()
    temp_path = settings.upload_dir / f"{job.id}.part"
    with temp_path.open("wb") as stream:
        stream.truncate(data.total_size)
    job.temp_path = str(temp_path)
    db.add(JobEvent(job_id=job.id, phase=job.status, message="上传任务已创建", progress=0))
    db.commit()
    db.refresh(job)
    return job


def save_chunk(
    db: Session,
    job: UploadJob,
    index: int,
    body: bytes,
    supplied_sha256: str,
) -> UploadJob:
    if job.status not in {UploadStatus.initialized.value, UploadStatus.uploading.value}:
        raise HTTPException(status_code=409, detail="当前任务不能接收分块")
    if index < 0 or index >= job.expected_chunks:
        raise HTTPException(status_code=400, detail="分块序号超出范围")
    expected_length = min(job.chunk_size, job.total_size - index * job.chunk_size)
    if len(body) != expected_length:
        raise HTTPException(status_code=400, detail="分块大小不正确")
    actual_sha = hashlib.sha256(body).hexdigest()
    if not supplied_sha256 or actual_sha.lower() != supplied_sha256.lower():
        raise HTTPException(status_code=422, detail="分块校验失败")
    previous = db.scalar(
        select(UploadChunk).where(UploadChunk.job_id == job.id, UploadChunk.chunk_index == index)
    )
    if previous is not None:
        if previous.sha256 != actual_sha:
            raise HTTPException(status_code=409, detail="该分块已存在但校验值不同")
        return job
    started = time.perf_counter()
    with Path(job.temp_path).open("r+b") as stream:
        stream.seek(index * job.chunk_size)
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    elapsed = max(time.perf_counter() - started, 0.001)
    db.add(
        UploadChunk(
            job_id=job.id,
            chunk_index=index,
            offset=index * job.chunk_size,
            byte_size=len(body),
            sha256=actual_sha,
        )
    )
    job.received_bytes += len(body)
    job.bytes_per_second = len(body) / elapsed
    remaining = max(job.total_size - job.received_bytes, 0)
    job.eta_seconds = round(remaining / job.bytes_per_second) if job.bytes_per_second else None
    job.progress = round(job.received_bytes / job.total_size * 100, 2)
    job.status = UploadStatus.uploading.value
    job.updated_at = utc_now()
    db.add(
        JobEvent(
            job_id=job.id,
            phase=job.status,
            message=f"已接收分块 {index + 1}/{job.expected_chunks}",
            progress=job.progress,
        )
    )
    db.commit()
    db.refresh(job)
    return job


def _verify_header(path: Path, file_name: str) -> None:
    with path.open("rb") as stream:
        header = stream.read(8)
    suffix = Path(file_name).suffix.lower()
    if suffix == ".exe" and not header.startswith(b"MZ"):
        raise ValueError("EXE 文件头无效")
    if suffix == ".msi" and header != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        raise ValueError("MSI 文件头无效")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def verify_upload(job_id: str) -> None:
    settings = get_settings()
    with SessionLocal() as db:
        job = db.get(UploadJob, job_id)
        if job is None:
            return
        try:
            chunks = db.scalar(
                select(func.count(UploadChunk.id)).where(UploadChunk.job_id == job.id)
            ) or 0
            if chunks != job.expected_chunks or job.received_bytes != job.total_size:
                raise ValueError("分块尚未全部上传")
            add_event(db, job, UploadStatus.verifying.value, "正在校验文件完整性与 PE 文件头", 96)
            path = Path(job.temp_path)
            if not path.is_file() or path.stat().st_size != job.total_size:
                raise ValueError("上传文件大小不一致")
            _verify_header(path, job.file_name)
            job.sha256 = _sha256(path)
            db.commit()
            add_event(db, job, UploadStatus.scanning.value, "正在通过 ClamAV 扫描", 98)
            scan_file(path, settings.clamav_host, settings.clamav_port, settings.clamav_timeout_seconds)
            release_dir = settings.release_dir / job.id
            release_dir.mkdir(parents=True, exist_ok=False)
            final_path = release_dir / job.file_name
            os.replace(path, final_path)
            release = Release(
                version=job.version,
                channel=job.channel,
                platform=job.platform,
                release_notes=job.release_notes,
                file_name=job.file_name,
                file_path=str(final_path),
                byte_size=job.total_size,
                sha256=job.sha256,
                uploaded_by=job.created_by,
            )
            db.add(release)
            add_event(db, job, UploadStatus.ready.value, "校验与扫描通过，等待发布", 100)
        except (ValueError, OSError, MalwareScanError) as exc:
            job.error_message = str(exc)
            add_event(db, job, UploadStatus.failed.value, str(exc), job.progress)


def cancel_upload(db: Session, job: UploadJob) -> None:
    if job.status in {UploadStatus.ready.value, UploadStatus.published.value}:
        raise HTTPException(status_code=409, detail="已校验任务不可取消")
    path = Path(job.temp_path)
    if path.exists():
        path.unlink()
    job.status = UploadStatus.cancelled.value
    job.error_message = "用户取消上传"
    db.add(JobEvent(job_id=job.id, phase=job.status, message="上传已取消", progress=job.progress))
    db.commit()
