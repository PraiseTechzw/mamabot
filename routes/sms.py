from flask import Blueprint, jsonify, request

from utils.validators import validate_message


def register(service):
    bp = Blueprint("sms", __name__, url_prefix="/sms")

    @bp.post("/inbound")
    def inbound():
        data = request.get_json(silent=True) or request.form
        try:
            text = validate_message(data.get("message", ""))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        sender = str(data.get("from", "sms-user"))
        reply = service.handle(text, sender, "sms")
        return jsonify({"text": reply.text, "intent": reply.intent, "escalation": reply.escalation})

    return bp
