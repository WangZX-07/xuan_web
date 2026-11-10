from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

from app.core.config import Settings


@dataclass(slots=True)
class FeishuUser:
    open_id: str
    tenant_key: str
    display_name: str
    avatar_url: str | None
    department_ids: list[str]


class FeishuClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def authorize_url(self, state: str) -> str:
        query = urlencode(
            {
                "app_id": self.settings.feishu_app_id,
                "redirect_uri": self.settings.feishu_redirect_uri,
                "state": state,
            }
        )
        return f"{self.settings.feishu_authorize_url}?{query}"

    async def _json(self, method: str, url: str, **kwargs) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="飞书身份服务暂时不可用") from exc
        if payload.get("code", 0) not in (0, None):
            raise HTTPException(status_code=403, detail="飞书身份校验失败")
        return payload

    async def exchange_code(self, code: str) -> str:
        payload = await self._json(
            "POST",
            self.settings.feishu_oauth_token_url,
            json={
                "grant_type": "authorization_code",
                "client_id": self.settings.feishu_app_id,
                "client_secret": self.settings.feishu_app_secret,
                "code": code,
                "redirect_uri": self.settings.feishu_redirect_uri,
            },
        )
        token = payload.get("access_token") or payload.get("data", {}).get("access_token")
        if not token:
            raise HTTPException(status_code=403, detail="未能取得飞书用户授权")
        return str(token)

    async def tenant_token(self) -> str:
        payload = await self._json(
            "POST",
            self.settings.feishu_tenant_token_url,
            json={"app_id": self.settings.feishu_app_id, "app_secret": self.settings.feishu_app_secret},
        )
        token = payload.get("tenant_access_token") or payload.get("data", {}).get("tenant_access_token")
        if not token:
            raise HTTPException(status_code=502, detail="无法核验飞书组织关系")
        return str(token)

    async def fetch_user(self, user_access_token: str) -> FeishuUser:
        info = await self._json(
            "GET",
            self.settings.feishu_user_info_url,
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        data = info.get("data", info)
        open_id = data.get("open_id")
        tenant_key = data.get("tenant_key")
        if not open_id or not tenant_key:
            raise HTTPException(status_code=403, detail="飞书身份信息不完整")
        tenant_access_token = await self.tenant_token()
        contact = await self._json(
            "GET",
            self.settings.feishu_contact_user_url.format(open_id=open_id),
            params={"user_id_type": "open_id", "department_id_type": "department_id"},
            headers={"Authorization": f"Bearer {tenant_access_token}"},
        )
        user = contact.get("data", {}).get("user", {})
        departments = [str(item) for item in user.get("department_ids", [])]
        return FeishuUser(
            open_id=str(open_id),
            tenant_key=str(tenant_key),
            display_name=str(data.get("name") or user.get("name") or "飞书用户"),
            avatar_url=data.get("avatar_url") or user.get("avatar", {}).get("avatar_240"),
            department_ids=departments,
        )

    def ensure_allowed(self, user: FeishuUser) -> None:
        if user.tenant_key not in self.settings.feishu_allowed_tenant_keys:
            raise HTTPException(status_code=403, detail="该飞书租户不在允许范围内")
        if not set(user.department_ids).intersection(self.settings.feishu_allowed_department_ids):
            raise HTTPException(status_code=403, detail="当前账号不属于获准部门")
