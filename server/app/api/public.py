from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Asset, AssetStatus, DownloadDaily, Release, ReleaseStatus
from app.services.content import get_published


router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/site")
def published_site(db: Session = Depends(get_db)):
    version, content = get_published(db)
    return {
        "content_version": version.version_number,
        "published_at": version.created_at,
        "content": content.model_dump(mode="json"),
    }


def current_release(db: Session) -> Release:
    release = db.scalar(
        select(Release).where(
            Release.is_current.is_(True),
            Release.status == ReleaseStatus.published.value,
        )
    )
    if release is None:
        raise HTTPException(status_code=404, detail="当前暂无公开体验版")
    return release


@router.get("/releases/latest")
def latest_release(db: Session = Depends(get_db)):
    release = db.scalar(
        select(Release).where(
            Release.is_current.is_(True),
            Release.status == ReleaseStatus.published.value,
        )
    )
    if release is None:
        return Response(status_code=204)
    return {
        "id": release.id,
        "version": release.version,
        "channel": release.channel,
        "platform": release.platform,
        "release_notes": release.release_notes,
        "file_name": release.file_name,
        "byte_size": release.byte_size,
        "sha256": release.sha256,
        "published_at": release.published_at,
        "download_url": f"/api/public/releases/{release.id}/download",
    }


def requested_size(range_header: str | None, total: int) -> int:
    if not range_header or not range_header.startswith("bytes="):
        return total
    try:
        first = range_header.removeprefix("bytes=").split(",", 1)[0]
        start_raw, end_raw = first.split("-", 1)
        if not start_raw:
            return min(int(end_raw), total)
        start = int(start_raw)
        end = min(int(end_raw), total - 1) if end_raw else total - 1
        return max(0, end - start + 1)
    except (ValueError, TypeError):
        return 0


@router.get("/releases/{release_id}/download")
def download_release(release_id: str, request: Request, db: Session = Depends(get_db)):
    release = db.get(Release, release_id)
    if release is None or release.status != ReleaseStatus.published.value:
        raise HTTPException(status_code=404, detail="版本不存在或尚未发布")
    counter = db.scalar(
        select(DownloadDaily).where(
            DownloadDaily.release_id == release.id,
            DownloadDaily.day == date.today(),
        )
    )
    if counter is None:
        counter = DownloadDaily(release_id=release.id, day=date.today())
        db.add(counter)
    counter.started_count += 1
    counter.requested_bytes += requested_size(request.headers.get("range"), release.byte_size)
    db.commit()
    response = Response(status_code=200)
    response.headers["X-Accel-Redirect"] = f"/_protected/releases/{release.id}/{quote(release.file_name)}"
    response.headers["Content-Type"] = "application/octet-stream"
    response.headers["Content-Disposition"] = (
        f"attachment; filename*=UTF-8''{quote(release.file_name)}"
    )
    response.headers["Accept-Ranges"] = "bytes"
    return response


@router.get("/assets/{asset_id}")
def public_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if asset is None or asset.status != AssetStatus.active.value:
        raise HTTPException(status_code=404, detail="素材不存在")
    response = Response(status_code=200)
    response.headers["X-Accel-Redirect"] = f"/_protected/assets/{asset.id}/{Path(asset.optimized_path).name}"
    response.headers["Content-Type"] = asset.mime_type if asset.optimized_path.endswith(".avif") else "image/webp"
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response
