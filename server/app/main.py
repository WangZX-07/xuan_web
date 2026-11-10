from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, assets, auth, content, public, releases
from app.core.config import get_settings
from app.core.database import SessionLocal, initialize_database
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.services.content import ensure_initial_content


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.validate_for_startup()
    initialize_database()
    with SessionLocal() as db:
        ensure_initial_content(db)
    yield


settings = get_settings()
app = FastAPI(
    title="LungTic Control Service",
    version="0.1.0",
    docs_url="/internal/docs" if settings.environment != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.public_origin, settings.admin_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "X-Chunk-SHA256"],
)
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(content.router)
app.include_router(assets.router)
app.include_router(releases.router)
app.include_router(releases.jobs_router)
app.include_router(admin.router)


@app.get("/healthz", include_in_schema=False)
def healthcheck():
    return {"status": "ok"}
