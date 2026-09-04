from flask import Blueprint, jsonify, request

from utils.validators import validate_message

bp = Blueprint("webhook", __name__)
def parse_message():
    data = request.get_json(silent=True) or {}
    return validate_message(data.get("message", "")), str(data.get("sender", "webhook-user")), str(data.get("language", "en"))
@bp.post("/webhook/message")
def message_webhook(): return jsonify({"error": "Use the channel-specific webhook adapters."}), 400
