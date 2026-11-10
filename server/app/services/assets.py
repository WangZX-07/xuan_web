from __future__ import annotations

import hashlib
import io
import shutil
from pathlib import Path

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Asset


ALLOWED = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),
    "image/avif": (b"\x00\x00\x00",),
}


def detect_image_mime(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if len(data) > 16 and data[4:12] in (b"ftypavif", b"ftypavis"):
        return "image/avif"
    return None


def save_asset(db: Session, file_name: str, data: bytes, alt_text: str, actor_id: str) -> Asset:
    settings = get_settings()
    if not data or len(data) > settings.asset_max_bytes:
        raise HTTPException(status_code=413, detail="图片为空或超过大小限制")
    mime = detect_image_mime(data)
    if mime not in ALLOWED:
        raise HTTPException(status_code=415, detail="仅支持 JPEG、PNG、WebP 和 AVIF")
    digest = hashlib.sha256(data).hexdigest()
    asset = Asset(
        original_name=Path(file_name).name,
        mime_type=mime,
        byte_size=len(data),
        sha256=digest,
        original_path="pending",
        optimized_path="pending",
        alt_text=alt_text.strip(),
        uploaded_by=actor_id,
    )
    if len(asset.alt_text) < 4:
        raise HTTPException(status_code=422, detail="请填写清晰的图片替代文本")
    db.add(asset)
    db.flush()
    folder = settings.asset_dir / asset.id
    folder.mkdir(parents=True, exist_ok=False)
    suffix = { "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/avif": ".avif" }[mime]
    original = folder / f"original{suffix}"
    original.write_bytes(data)
    optimized = folder / "optimized.webp"
    if mime == "image/avif":
        optimized = original
    else:
        try:
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
            with Image.open(io.BytesIO(data)) as image:
                image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGBA" if "transparency" in image.info else "RGB")
                image.save(optimized, "WEBP", quality=84, method=6)
        except (UnidentifiedImageError, OSError) as exc:
            shutil.rmtree(folder, ignore_errors=True)
            raise HTTPException(status_code=415, detail="图片内容损坏或格式不匹配") from exc
    asset.original_path = str(original)
    asset.optimized_path = str(optimized)
    db.commit()
    db.refresh(asset)
    return asset
