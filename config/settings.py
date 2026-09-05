"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    secret_key: str = os.getenv("SECRET_KEY", "local-development-only")
    admin_token: str = os.getenv("ADMIN_TOKEN", "")
    flask_env: str = os.getenv("FLASK_ENV", "development")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "5000"))
    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_database: str = os.getenv("MYSQL_DATABASE", "mamabot")
    mysql_user: str = os.getenv("MYSQL_USER", "mamabot")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    database_backend: str = os.getenv("DATABASE_BACKEND", "memory").strip().lower()
    smspop_base_url: str = os.getenv("SMSPOP_BASE_URL", "https://api.sms-pop.co.zw")
    smspop_api_key: str = os.getenv("SMSPOP_API_KEY", "")
    smspop_sender_id: str = os.getenv("SMSPOP_SENDER_ID", "MamaBot")
    smspop_webhook_token: str = os.getenv("SMSPOP_WEBHOOK_TOKEN", "")
    nurse_phone_number: str = os.getenv("NURSE_PHONE_NUMBER", "")
    whatsapp_provider: str = os.getenv("WHATSAPP_PROVIDER", "console")
    whatsapp_access_token: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    reminder_timezone: str = os.getenv("REMINDER_TIMEZONE", "Africa/Harare")
    reminder_hour: int = int(os.getenv("REMINDER_HOUR", "8"))
    reminder_minute: int = int(os.getenv("REMINDER_MINUTE", "0"))
    enable_reminder_scheduler: bool = _as_bool(os.getenv("ENABLE_REMINDER_SCHEDULER"))

    @property
    def mysql_config(self) -> dict[str, object]:
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "database": self.mysql_database,
            "user": self.mysql_user,
            "password": self.mysql_password,
        }


settings = Settings()
