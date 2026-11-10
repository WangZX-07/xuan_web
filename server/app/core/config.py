from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LUNGTIC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 9100
    public_origin: str = "https://respulse.top"
    admin_origin: str = "https://console.respulse.top"
    database_url: str = "sqlite:///./runtime/lungtic.sqlite3"
    data_dir: Path = Path("./runtime")
    release_dir: Path | None = None
    asset_dir: Path | None = None
    upload_dir: Path | None = None
    backup_dir: Path | None = None

    session_cookie_name: str = "lungtic_admin_session"
    oauth_cookie_name: str = "lungtic_feishu_state"
    csrf_cookie_name: str = "lungtic_csrf"
    session_ttl_hours: int = 12
    session_cookie_secure: bool = True
    csrf_header_name: str = "X-CSRF-Token"
    ip_hash_salt: str = Field(default="", repr=False)

    feishu_app_id: str = Field(default="", repr=False)
    feishu_app_secret: str = Field(default="", repr=False)
    feishu_allowed_tenant_keys: list[str] = Field(default_factory=list)
    feishu_allowed_department_ids: list[str] = Field(default_factory=list)
    feishu_owner_open_ids: list[str] = Field(default_factory=list)
    feishu_redirect_uri: str = "https://console.respulse.top/auth/feishu/callback"
    feishu_authorize_url: str = "https://accounts.feishu.cn/open-apis/authen/v1/authorize"
    feishu_oauth_token_url: str = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
    feishu_user_info_url: str = "https://open.feishu.cn/open-apis/authen/v1/user_info"
    feishu_tenant_token_url: str = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    feishu_contact_user_url: str = "https://open.feishu.cn/open-apis/contact/v3/users/{open_id}"

    clamav_host: str = "127.0.0.1"
    clamav_port: int = 3310
    clamav_timeout_seconds: int = 180
    upload_chunk_size: int = 8 * 1024 * 1024
    upload_max_bytes: int = 1024 * 1024 * 1024
    asset_max_bytes: int = 24 * 1024 * 1024
    minimum_free_bytes: int = 2 * 1024 * 1024 * 1024

    @field_validator(
        "feishu_allowed_tenant_keys",
        "feishu_allowed_department_ids",
        "feishu_owner_open_ids",
        mode="before",
    )
    @classmethod
    def parse_csv_list(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def prepare_directories(self) -> None:
        self.data_dir = self.data_dir.resolve()
        self.release_dir = (self.release_dir or self.data_dir / "releases").resolve()
        self.asset_dir = (self.asset_dir or self.data_dir / "assets").resolve()
        self.upload_dir = (self.upload_dir or self.data_dir / "uploads").resolve()
        self.backup_dir = (self.backup_dir or self.data_dir / "backups").resolve()
        for path in (
            self.data_dir,
            self.release_dir,
            self.asset_dir,
            self.upload_dir,
            self.backup_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"

    @property
    def feishu_configured(self) -> bool:
        return bool(
            self.feishu_app_id
            and self.feishu_app_secret
            and self.feishu_allowed_tenant_keys
            and self.feishu_allowed_department_ids
        )

    def validate_for_startup(self) -> None:
        if self.environment != "production":
            return
        errors: list[str] = []
        if not self.feishu_configured:
            errors.append("飞书应用、租户和部门配置不完整")
        if not self.feishu_owner_open_ids:
            errors.append("至少需要配置一个初始所有者 open_id")
        if len(self.ip_hash_salt) < 32:
            errors.append("IP 哈希盐长度至少为 32 个字符")
        if not self.session_cookie_secure:
            errors.append("生产环境必须启用 Secure 会话 Cookie")
        if self.host not in {"127.0.0.1", "localhost"}:
            errors.append("控制服务只能监听回环地址")
        if errors:
            raise RuntimeError("生产配置校验失败：" + "；".join(errors))


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.prepare_directories()
    return settings
