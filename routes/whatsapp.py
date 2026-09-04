from flask import Blueprint, jsonify, request

from utils.validators import validate_message


def register(service):
    bp = Blueprint("whatsapp", __name__, url_prefix="/whatsapp")

    @bp.post("/webhook")
    def webhook():
        data = request.get_json(silent=True) or {}
        try:
            text = validate_message(data.get("message", ""))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        reply = service.handle(text, str(data.get("from", "whatsapp-user")), "whatsapp")
        return jsonify({"text": reply.text, "intent": reply.intent, "escalation": reply.escalation})

    return bp
