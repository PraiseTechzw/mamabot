from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from app import db
from app.routes.auth import login_required
from app.nlp.engine import get_nlp
from app.routes.webhook import detect_lang
from app.services.reminders import (
    schedule_appointment_reminders,
    schedule_reminder,
    schedule_weekly_pregnancy_reminders,
)
from app.services.messaging import MessagingError, send_sms, validate_phone_number

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/retrain", methods=["POST"])
@login_required
def retrain():
    """Force retrain the NLP model — call after editing intents.json."""
    nlp = get_nlp()
    nlp.retrain()
    return jsonify({"status": "ok", "message": "Model retrained successfully."})

@admin_bp.route("/test-nlp", methods=["GET"])
@login_required
def test_nlp():
    """Quick sanity check — tests a few sample sentences."""
    nlp = get_nlp()
    samples = [
        "I am having heavy bleeding",
        "Ndiri nani kana ndine mimba?",
        "what should I eat during pregnancy",
        "find nearest clinic",
        "sawubona ngidinga usizo"
    ]
    results = []
    for s in samples:
        intent, conf = nlp.predict_intent(s)
        lang = detect_lang(s) or "english"
        results.append({
            "input": s,
            "intent": intent,
            "confidence": round(conf, 3),
            "language": lang,
            "response_preview": nlp.get_response(intent, lang)[:80] + "..."
        })
    return jsonify(results)


@admin_bp.route("/patients", methods=["POST"])
@login_required
def upsert_patient():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required"}), 400

    phone_number = data.get("phone_number")
    if not isinstance(phone_number, str):
        return jsonify({"error": "phone_number is required"}), 400
    phone_number = phone_number.strip()
    language = data.get("preferred_lang", "english")
    consent = data.get("consent")
    consent_source = data.get("consent_source")
    due_date = data.get("due_date")

    try:
        validate_phone_number(phone_number)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if language not in {"english", "shona", "ndebele"}:
        return jsonify({"error": "preferred_lang must be english, shona, or ndebele"}), 400
    if not isinstance(consent, bool):
        return jsonify({"error": "consent must be explicitly true or false"}), 400
    if consent and not consent_source:
        return jsonify({"error": "consent_source is required when consent is true"}), 400
    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except (TypeError, ValueError):
            return jsonify({"error": "due_date must use YYYY-MM-DD format"}), 400

    patient = {
        "phone_number": phone_number,
        "preferred_lang": language,
        "preferred_channel": "whatsapp",
        "due_date": due_date,
        "reminders_enabled": consent,
        "consent_at": datetime.now(timezone.utc).isoformat() if consent else None,
        "consent_source": consent_source if consent else None,
    }
    try:
        saved = db.upsert_patient(patient)
        if not consent:
            db.cancel_pending_reminders(phone_number)
    except Exception:
        current_app.logger.exception("Could not save patient")
        return jsonify({"error": "could not save patient"}), 503
    return jsonify({
        "phone_number": saved["phone_number"],
        "reminders_enabled": saved["reminders_enabled"],
        "due_date": saved.get("due_date"),
    }), 201


@admin_bp.route("/reminders", methods=["POST"])
@login_required
def create_reminder():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required"}), 400
    try:
        reminder = schedule_reminder(
            data.get("phone_number", ""),
            data.get("content", ""),
            data.get("scheduled_at", ""),
            data.get("category", "general"),
        )
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Could not schedule reminder")
        return jsonify({"error": "could not schedule reminder"}), 503
    return jsonify(reminder), 201


@admin_bp.route("/appointments", methods=["POST"])
@login_required
def create_appointment():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required"}), 400
    try:
        appointment = schedule_appointment_reminders(
            data.get("phone_number", ""),
            data.get("appointment_at", ""),
            data.get("reminder_message", ""),
            data.get("clinic_name"),
        )
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Could not schedule appointment reminders")
        return jsonify({"error": "could not schedule appointment reminders"}), 503
    return jsonify(appointment), 201


@admin_bp.route("/pregnancy-reminders", methods=["POST"])
@login_required
def create_pregnancy_reminders():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required"}), 400
    try:
        reminders = schedule_weekly_pregnancy_reminders(
            data.get("phone_number", ""),
            data.get("messages"),
        )
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Could not schedule weekly pregnancy reminders")
        return jsonify({"error": "could not schedule weekly pregnancy reminders"}), 503
    return jsonify({"scheduled": len(reminders), "reminders": reminders}), 201


@admin_bp.route("/sms", methods=["POST"])
@login_required
def send_sms_message():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required"}), 400
    try:
        result = send_sms(
            data.get("phone_number", ""),
            data.get("message", ""),
            campaign_name=data.get("campaign_name", "MamaBot message"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except MessagingError as exc:
        current_app.logger.error("SMSPoP send failed: %s", exc)
        return jsonify({"error": str(exc)}), 502

    return jsonify({
        "provider": result.provider,
        "message_id": result.message_id,
        "status": result.status,
    }), 202
