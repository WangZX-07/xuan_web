from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import EditorAdmin
from app.models.entities import Asset, AssetStatus
from app.services.assets import save_asset
from app.services.audit import write_audit


router = APIRouter(prefix="/api/admin/assets", tags=["admin-assets"])


def asset_response(asset: Asset) -> dict:
    return {
        "id": asset.id,
        "original_name": asset.original_name,
        "mime_type": asset.mime_type,
        "byte_size": asset.byte_size,
        "sha256": asset.sha256,
        "alt_text": asset.alt_text,
        "status": asset.status,
        "url": f"/api/public/assets/{asset.id}",
        "created_at": asset.created_at,
    }


@router.get("")
def list_assets(admin: EditorAdmin, db: Session = Depends(get_db)):
    assets = db.scalars(select(Asset).order_by(Asset.created_at.desc()).limit(200)).all()
    return [asset_response(item) for item in assets]


@router.post("")
async def upload_asset(
    request: Request,
    admin: EditorAdmin,
    file: UploadFile = File(...),
    alt_text: str = Form(...),
    db: Session = Depends(get_db),
):
    data = await file.read()
    asset = save_asset(db, file.filename or "asset", data, alt_text, admin.identity.id)
    write_audit(db, request, admin, "asset.upload", "asset", asset.id, {"name": asset.original_name})
    db.commit()
    return asset_response(asset)


@router.post("/{asset_id}/archive")
def archive_asset(
    asset_id: str,
    request: Request,
    admin: EditorAdmin,
    db: Session = Depends(get_db),
):
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="素材不存在")
    asset.status = AssetStatus.archived.value
    write_audit(db, request, admin, "asset.archive", "asset", asset.id)
    db.commit()
    return {"ok": True}
