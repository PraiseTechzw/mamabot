"""SMSPoP delivery-report webhook."""

import json
import logging

from flask import Blueprint, current_app, jsonify, request

from app import db
from app.services.messaging import verify_smspop_signature

logger = logging.getLogger(__name__)
smspop_bp = Blueprint("smspop", __name__)


@smspop_bp.route("/webhook/smspop/delivery-reports", methods=["POST"])
def delivery_report():
    raw_body = request.get_data(cache=True)
    timestamp = request.headers.get("X-SmsPop-Timestamp", "")
    signature = request.headers.get("X-SmsPop-Signature", "")
    secret = current_app.config.get("SMSPOP_WEBHOOK_SECRET")

    if not secret:
        return jsonify({"error": "SMSPoP webhook is not configured"}), 503
    if not verify_smspop_signature(raw_body, timestamp, signature, secret):
        return jsonify({"error": "invalid webhook signature"}), 401

    try:
        report = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return jsonify({"error": "invalid JSON"}), 400

    if request.headers.get("X-SmsPop-Event") != report.get("event"):
        return jsonify({"error": "event header does not match payload"}), 400
    if report.get("event") == "webhook.test":
        return jsonify({"status": "ok"}), 200
    if report.get("event") != "message.delivery_report":
        return jsonify({"error": "unsupported event"}), 400

    required = ("webhook_id", "message_id", "phone", "status")
    if any(field not in report for field in required):
        return jsonify({"error": "delivery report is missing required fields"}), 400
    valid_statuses = {"delivered", "undelivered", "expired", "rejected", "unknown"}
    if (
        not isinstance(report["webhook_id"], int)
        or not isinstance(report["message_id"], int)
        or not isinstance(report["phone"], str)
        or not report["phone"]
        or report["status"] not in valid_statuses
    ):
        return jsonify({"error": "delivery report fields are invalid"}), 400

    try:
        db.save_sms_delivery_report(report)
    except Exception:
        logger.exception("Could not save SMSPoP delivery report")
        return jsonify({"error": "could not save delivery report"}), 503
    return jsonify({"status": "ok"}), 200
