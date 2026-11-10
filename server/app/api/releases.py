from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import OwnerAdmin, PublisherAdmin
from app.models.entities import (
    JobEvent,
    Release,
    ReleaseStatus,
    UploadJob,
    UploadStatus,
    utc_now,
)
from app.schemas.release import (
    DeleteReleaseRequest,
    PublishRequest,
    ReleaseResponse,
    UploadInitializeRequest,
    UploadJobResponse,
)
from app.services.audit import write_audit
from app.services.uploads import cancel_upload, initialize_upload, save_chunk, verify_upload


router = APIRouter(prefix="/api/admin/releases", tags=["admin-releases"])
jobs_router = APIRouter(prefix="/api/admin/jobs", tags=["admin-jobs"])


@router.get("", response_model=list[ReleaseResponse])
def list_releases(admin: PublisherAdmin, db: Session = Depends(get_db)):
    return db.scalars(select(Release).order_by(Release.created_at.desc()).limit(200)).all()


@router.get("/uploads", response_model=list[UploadJobResponse])
def list_uploads(admin: PublisherAdmin, db: Session = Depends(get_db)):
    return db.scalars(select(UploadJob).order_by(UploadJob.created_at.desc()).limit(100)).all()


@router.post("/uploads", response_model=UploadJobResponse)
def create_upload(
    payload: UploadInitializeRequest,
    request: Request,
    admin: PublisherAdmin,
    db: Session = Depends(get_db),
):
    job = initialize_upload(db, payload, admin.identity.id)
    write_audit(db, request, admin, "release.upload.initialize", "upload_job", job.id)
    db.commit()
    return job


@router.get("/uploads/{job_id}", response_model=UploadJobResponse)
def get_upload(job_id: str, admin: PublisherAdmin, db: Session = Depends(get_db)):
    job = db.get(UploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    return job


@router.put("/uploads/{job_id}/chunks/{index}", response_model=UploadJobResponse)
async def put_chunk(
    job_id: str,
    index: int,
    request: Request,
    admin: PublisherAdmin,
    x_chunk_sha256: str = Header(alias="X-Chunk-SHA256"),
    db: Session = Depends(get_db),
):
    job = db.get(UploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    body = await request.body()
    return save_chunk(db, job, index, body, x_chunk_sha256)


@router.post("/uploads/{job_id}/complete", response_model=UploadJobResponse)
def complete_upload(
    job_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    admin: PublisherAdmin,
    db: Session = Depends(get_db),
):
    job = db.get(UploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    if job.received_bytes != job.total_size:
        raise HTTPException(status_code=409, detail="分块尚未全部上传")
    if job.status in {UploadStatus.verifying.value, UploadStatus.scanning.value}:
        return job
    write_audit(db, request, admin, "release.upload.complete", "upload_job", job.id)
    db.commit()
    background_tasks.add_task(verify_upload, job.id)
    return job


@router.post("/uploads/{job_id}/cancel")
def cancel_upload_route(
    job_id: str,
    request: Request,
    admin: PublisherAdmin,
    db: Session = Depends(get_db),
):
    job = db.get(UploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    cancel_upload(db, job)
    write_audit(db, request, admin, "release.upload.cancel", "upload_job", job.id)
    db.commit()
    return {"ok": True}


@router.get("/uploads/{job_id}/events")
@jobs_router.get("/{job_id}/events")
async def upload_events(job_id: str, admin: PublisherAdmin):
    async def stream():
        cursor = 0
        idle = 0
        while idle < 600:
            with SessionLocal() as db:
                job = db.get(UploadJob, job_id)
                if job is None:
                    yield "event: error\ndata: {\"message\":\"任务不存在\"}\n\n"
                    return
                events = db.scalars(
                    select(JobEvent)
                    .where(JobEvent.job_id == job_id, JobEvent.id > cursor)
                    .order_by(JobEvent.id.asc())
                ).all()
                for event in events:
                    cursor = event.id
                    payload = json.dumps(
                        {
                            "id": event.id,
                            "phase": event.phase,
                            "message": event.message,
                            "progress": event.progress,
                            "created_at": event.created_at.isoformat(),
                        },
                        ensure_ascii=False,
                    )
                    yield f"id: {event.id}\nevent: progress\ndata: {payload}\n\n"
                if job.status in {
                    UploadStatus.ready.value,
                    UploadStatus.failed.value,
                    UploadStatus.cancelled.value,
                    UploadStatus.published.value,
                }:
                    yield f"event: complete\ndata: {json.dumps({'status': job.status})}\n\n"
                    return
            idle += 1
            yield ": keep-alive\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/{release_id}/publish", response_model=ReleaseResponse)
def publish_release(
    release_id: str,
    payload: PublishRequest,
    request: Request,
    admin: PublisherAdmin,
    db: Session = Depends(get_db),
):
    release = db.get(Release, release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="版本不存在")
    if release.status == ReleaseStatus.archived.value:
        raise HTTPException(status_code=409, detail="已归档版本需先恢复")
    if payload.make_current:
        current = db.scalars(select(Release).where(Release.is_current.is_(True))).all()
        for item in current:
            item.is_current = False
    release.status = ReleaseStatus.published.value
    release.is_current = payload.make_current
    release.published_by = admin.identity.id
    release.published_at = utc_now()
    upload = db.scalar(select(UploadJob).where(UploadJob.id == Path(release.file_path).parent.name))
    if upload is not None:
        upload.status = UploadStatus.published.value
    write_audit(
        db,
        request,
        admin,
        "release.publish",
        "release",
        release.id,
        {"version": release.version, "make_current": payload.make_current},
    )
    db.commit()
    db.refresh(release)
    return release


@router.post("/{release_id}/set-current", response_model=ReleaseResponse)
def set_current(
    release_id: str,
    request: Request,
    admin: PublisherAdmin,
    db: Session = Depends(get_db),
):
    release = db.get(Release, release_id)
    if release is None or release.status != ReleaseStatus.published.value:
        raise HTTPException(status_code=409, detail="只能将已发布版本设为当前版本")
    for item in db.scalars(select(Release).where(Release.is_current.is_(True))).all():
        item.is_current = False
    release.is_current = True
    write_audit(
        db, request, admin, "release.set_current", "release", release.id, {"version": release.version}
    )
    db.commit()
    db.refresh(release)
    return release


@router.post("/{release_id}/archive")
def archive_release(
    release_id: str,
    request: Request,
    admin: PublisherAdmin,
    db: Session = Depends(get_db),
):
    release = db.get(Release, release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="版本不存在")
    if release.is_current:
        raise HTTPException(status_code=409, detail="当前公开版本不能归档，请先切换版本")
    release.status = ReleaseStatus.archived.value
    release.archived_at = utc_now()
    write_audit(db, request, admin, "release.archive", "release", release.id)
    db.commit()
    return {"ok": True}


@router.delete("/{release_id}")
def delete_release(
    release_id: str,
    payload: DeleteReleaseRequest,
    request: Request,
    admin: OwnerAdmin,
    db: Session = Depends(get_db),
):
    release = db.get(Release, release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="版本不存在")
    if release.status != ReleaseStatus.archived.value or release.is_current:
        raise HTTPException(status_code=409, detail="只有非当前的已归档版本可以永久删除")
    expected = f"永久删除 {release.version}"
    if payload.confirmation != expected:
        raise HTTPException(status_code=422, detail=f"请输入“{expected}”确认")
    folder = Path(release.file_path).parent.resolve()
    write_audit(
        db,
        request,
        admin,
        "release.delete",
        "release",
        release.id,
        {"version": release.version, "sha256": release.sha256},
    )
    db.delete(release)
    db.commit()
    if folder.is_dir():
        shutil.rmtree(folder)
    return {"ok": True}
