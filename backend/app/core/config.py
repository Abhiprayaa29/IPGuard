import base64
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
# Exactly 32 bytes (256 bits) deterministic key for local development/test environments
DEV_DEFAULT_NOTES_KEY = b"IPGuardDevMasterKey32BytesLong!!"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "IPGuard"
    app_version: str = "1.0.0"
    app_env: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = Field(min_length=1)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    trusted_origins: str | None = None
    dev_admin_key: str = "ipguard-dev-admin-secret-key"
    notes_master_key_b64: str | None = Field(
        default=None,
        description="Base64 encoded 32-byte master key for Secure Notes encryption.",
    )

    @property
    def notes_master_key_bytes(self) -> bytes:
        """
        Resolve the 32-byte master key for Secure Notes encryption.
        Fails closed in production if not explicitly set or not valid 32-byte Base64.
        """
        if not self.notes_master_key_b64:
            if self.app_env == "production":
                raise ValueError(
                    "CRITICAL: NOTES_MASTER_KEY_B64 is mandatory in production environments."
                )
            return DEV_DEFAULT_NOTES_KEY

        try:
            raw_key = base64.b64decode(self.notes_master_key_b64, validate=True)
        except Exception as err:
            raise ValueError(
                "NOTES_MASTER_KEY_B64 must be a valid Base64 encoded string."
            ) from err

        if len(raw_key) != 32:
            raise ValueError(
                f"NOTES_MASTER_KEY_B64 must decode to exactly 32 bytes (got {len(raw_key)})."
            )

        return raw_key

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def trusted_origin_list(self) -> list[str]:
        raw = self.trusted_origins if self.trusted_origins else self.cors_origins
        return [
            origin.strip()
            for origin in raw.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
