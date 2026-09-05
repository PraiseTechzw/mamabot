"""Test webhook — stateful conversational endpoint for development and
acceptance testing.  Accepts POST requests and routes them through the full
dialogue pipeline, including the registration flow.

POST /webhook/test
{
    "message": "register",
    "sender": "0771234567",    // optional; defaults to "webhook-user"
    "language": "en",          // optional; used for NLP hint only
    "channel": "test"          // optional; defaults to "test"
}

Response:
{
    "text": "...",
    "language": "en",
    "intent": "registration",
    "confidence": 1.0,
    "escalation": false
}
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from utils.validators import validate_message

bp = Blueprint("webhook", __name__)


def parse_message():
    data = request.get_json(silent=True) or {}
    return (
        validate_message(data.get("message", "")),
        str(data.get("sender", "webhook-user")),
        str(data.get("language", "en")),
        str(data.get("channel", "test")),
    )


@bp.post("/webhook/message")
def message_webhook():
    return jsonify({"error": "Use the channel-specific webhook adapters."}), 400


@bp.post("/webhook/test")
def test_webhook():
    """Stateful test endpoint that exercises the full conversation pipeline."""
    from flask import current_app

    service = current_app.extensions.get("mamabot_service")
    if service is None:
        return jsonify({"error": "Service not initialised."}), 500

    data = request.get_json(silent=True) or {}
    try:
        text = validate_message(data.get("message", ""))
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400

    sender = str(data.get("sender", "webhook-user"))
    language = str(data.get("language", "en"))
    channel = str(data.get("channel", "test"))

    reply = service.handle(text, sender, channel, language)
    return jsonify(
        {
            "text": reply.text,
            "language": reply.language,
            "intent": reply.intent,
            "confidence": round(reply.confidence, 3),
            "escalation": reply.escalation,
        }
    )
