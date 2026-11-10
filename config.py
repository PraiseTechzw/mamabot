import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def validate_production_config(values):
    """Reject incomplete production configuration before serving requests."""
    errors = []

    def is_placeholder(value):
        lowered = value.strip().lower()
        return any(
            marker in lowered
            for marker in (
                "replace-with-",
                "your-project",
                "change-me",
                "placeholder",
                "server-side-service-role-key",
            )
        )

    required = ("SECRET_KEY", "ADMIN_PASSWORD", "SUPABASE_URL", "SUPABASE_KEY")
    for name in required:
        value = values.get(name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{name} must be configured")
        elif is_placeholder(value):
            errors.append(f"{name} must not use a placeholder value")

    secret_key = values.get("SECRET_KEY")
    if isinstance(secret_key, str) and secret_key.strip() and len(secret_key) < 32:
        errors.append("SECRET_KEY must be at least 32 characters long")

    admin_password = values.get("ADMIN_PASSWORD")
    if isinstance(admin_password, str) and admin_password.strip() and len(admin_password) < 12:
        errors.append("ADMIN_PASSWORD must be at least 12 characters long")

    supabase_url = values.get("SUPABASE_URL")
    if isinstance(supabase_url, str) and supabase_url.strip():
        parsed_url = urlparse(supabase_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            errors.append("SUPABASE_URL must be an absolute HTTP(S) URL")

    smspop_enabled = any(values.get(name) for name in ("SMSPOP_API_TOKEN", "SMSPOP_SENDER_ID"))
    if smspop_enabled:
        for name in ("SMSPOP_API_TOKEN", "SMSPOP_SENDER_ID"):
            if not values.get(name):
                errors.append(f"{name} is required when SMSPoP is enabled")
    if values.get("SMSPOP_DELIVERY_REPORT_URL") and not values.get("SMSPOP_WEBHOOK_SECRET"):
        errors.append("SMSPOP_WEBHOOK_SECRET is required when delivery reports are enabled")

    twilio_reminder_settings = (
        "TWILIO_ACCOUNT_SID",
        "TWILIO_WHATSAPP_NUMBER",
        "TWILIO_WHATSAPP_REMINDER_CONTENT_SID",
    )
    if any(values.get(name) for name in twilio_reminder_settings):
        for name in ("TWILIO_AUTH_TOKEN", *twilio_reminder_settings):
            if not values.get(name):
                errors.append(f"{name} is required when Twilio WhatsApp reminders are enabled")

    if errors:
        raise RuntimeError("Invalid production configuration: " + "; ".join(errors))


class Config:
    SECRET_KEY             = os.environ.get("SECRET_KEY")
    # Twilio — WhatsApp
    TWILIO_ACCOUNT_SID     = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    TWILIO_WHATSAPP_REMINDER_CONTENT_SID = os.environ.get("TWILIO_WHATSAPP_REMINDER_CONTENT_SID")
    TWILIO_WEBHOOK_BASE_URL = os.environ.get("TWILIO_WEBHOOK_BASE_URL")
    # SMSPoP — outbound Zimbabwe SMS
    SMSPOP_API_TOKEN       = os.environ.get("SMSPOP_API_TOKEN")
    SMSPOP_SENDER_ID       = os.environ.get("SMSPOP_SENDER_ID")
    SMSPOP_WEBHOOK_SECRET  = os.environ.get("SMSPOP_WEBHOOK_SECRET")
    SMSPOP_DELIVERY_REPORT_URL = os.environ.get("SMSPOP_DELIVERY_REPORT_URL")
    # Supabase
    SUPABASE_URL           = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY           = os.environ.get("SUPABASE_KEY")
    # Admin
    ADMIN_PASSWORD         = os.environ.get("ADMIN_PASSWORD")
    CONFIDENCE_THRESHOLD   = float(os.environ.get("CONFIDENCE_THRESHOLD", 0.38))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
