"""MamaBot Flask application."""

from __future__ import annotations

import atexit
import logging
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from config import settings
from database.queries import repository
from dialogue.manager import DialogueManager
from messaging.sms_provider import MockSmsPopProvider, SmsPopProvider
from messaging.whatsapp_provider import MockWhatsAppProvider, WhatsAppProvider
from reminders.scheduler import shutdown_scheduler, start_scheduler
from routes.admin import bp as admin_bp
from routes.health import bp as health_bp
from routes.sms import register as register_sms
from routes.webhook import bp as webhook_bp
from routes.whatsapp import register as register_whatsapp
from services.message_service import MessageService
from utils.validators import validate_message

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder="frontend", static_url_path="/static")
    app.config.from_mapping(
        SECRET_KEY=settings.secret_key,
        TESTING=False,
        ADMIN_TOKEN=settings.admin_token,
    )
    if test_config:
        app.config.update(test_config)

    manager = DialogueManager(app.config.get("MAMABOT_REPOSITORY", repository))
    service = MessageService(manager)
    app.extensions["mamabot_service"] = service

    @app.get("/")
    def index():
        return send_from_directory(ROOT / "frontend", "index.html")

    @app.post("/api/chat")
    def chat():
        data = request.get_json(silent=True) or {}
        try:
            text = validate_message(data.get("message", ""))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        language = str(data.get("language", "en"))
        reply = service.handle(text, "local-user", "browser", language)
        return jsonify(
            {
                "text": reply.text,
                "language": reply.language,
                "intent": reply.intent,
                "confidence": round(reply.confidence, 3),
                "escalation": reply.escalation,
            }
        )

    @app.errorhandler(500)
    def internal_error(error):
        log.exception("Unhandled application error", exc_info=error)
        return jsonify({"error": "The service could not process that request."}), 500

    app.register_blueprint(health_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(webhook_bp)
    sms_provider = app.config.get("SMS_PROVIDER")
    if sms_provider is None:
        sms_provider = (
            SmsPopProvider(settings.smspop_api_key, settings.smspop_sender_id)
            if settings.smspop_api_key
            else MockSmsPopProvider()
        )
    app.register_blueprint(register_sms(service, sms_provider))
    whatsapp_provider = app.config.get("WHATSAPP_PROVIDER_INSTANCE")
    if whatsapp_provider is None:
        whatsapp_provider = (
            WhatsAppProvider(
                settings.whatsapp_access_token,
                settings.whatsapp_phone_number_id,
            )
            if settings.whatsapp_provider.lower() not in {"console", "mock", ""}
            else MockWhatsAppProvider()
        )
    app.register_blueprint(register_whatsapp(service, whatsapp_provider))
    if settings.enable_reminder_scheduler and not app.testing:
        start_scheduler(app.config.get("REMINDER_PROVIDERS", {}))
    return app


app = create_app()
atexit.register(shutdown_scheduler)

if __name__ == "__main__":
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.flask_env == "development",
    )
