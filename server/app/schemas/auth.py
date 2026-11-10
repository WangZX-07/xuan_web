from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AdminIdentityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    avatar_url: str | None
    role: Literal["editor", "publisher", "owner"]
    expires_at: datetime
    csrf_token: str


class RoleUpdateRequest(BaseModel):
    role: Literal["editor", "publisher", "owner"]
