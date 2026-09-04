"""MamaBot Flask application."""
from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from config import settings
from database.queries import repository
from dialogue.manager import DialogueManager
from routes.admin import bp as admin_bp
from routes.health import bp as health_bp
from routes.sms import register as register_sms
from routes.whatsapp import register as register_whatsapp
from services.message_service import MessageService
from utils.validators import validate_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder="frontend", static_url_path="/static")
    app.config.from_mapping(SECRET_KEY=settings.secret_key, TESTING=False)
    if test_config:
        app.config.update(test_config)

    manager = DialogueManager(repository)
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
        return jsonify({
            "text": reply.text,
            "language": reply.language,
            "intent": reply.intent,
            "confidence": round(reply.confidence, 3),
            "escalation": reply.escalation,
        })

    @app.errorhandler(500)
    def internal_error(error):
        log.exception("Unhandled application error", exc_info=error)
        return jsonify({"error": "The service could not process that request."}), 500

    app.register_blueprint(health_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(register_sms(service))
    app.register_blueprint(register_whatsapp(service))
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.flask_env == "development")
