"""
app/routes/dashboard.py
Admin pages + public chat endpoint — Supabase version.
"""

from flask import Blueprint, render_template, jsonify, request, session, redirect
from app.routes.auth import login_required
from app.services.clinical_safety import with_safety_notice
import json, os, time, logging, sys

logger       = logging.getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)
_start_time  = time.time()

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
INTENTS_PATH = os.path.join(BASE_DIR, "data", "intents", "intents.json")
MODEL_PATH   = os.path.join(BASE_DIR, "instance", "nlp_model.pkl")


def _load_intents():
    try:
        with open(INTENTS_PATH) as f:
            return json.load(f)
    except:
        return {"intents": []}

def _count_samples():
    return sum(len(i["patterns"]) for i in _load_intents()["intents"])

def _count_intents():
    return len(_load_intents()["intents"])

def _uptime():
    s = int(time.time() - _start_time)
    h, rem = divmod(s, 3600)
    return f"{h}h {rem//60}m"


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@dashboard_bp.route("/chat")
def page_chat():
    return render_template("chat.html")


@dashboard_bp.route("/healthz")
def readiness():
    """Public readiness probe for hosting platforms."""
    from app.db import test_connection

    database_ok, _ = test_connection()
    status = "ok" if database_ok else "not_ready"
    return jsonify({"status": status, "checks": {"database": status}}), (
        200 if database_ok else 503
    )


@dashboard_bp.route("/chat/send", methods=["POST"])
def chat_send():
    """Public web chat endpoint — full language + context support."""
    data       = request.get_json() or {}
    message    = (data.get("message") or "").strip()
    session_id = data.get("session_id", "anonymous")
    language   = data.get("language", "english")

    if not message:
        return jsonify({"response": "Please send a message."}), 400

    # Use Flask session for web chat context memory
    sess_key = f"ctx_{session_id}"
    if sess_key not in session:
        session[sess_key] = {"language": language, "last_intent": None}
    ctx = session[sess_key]

    # Apply language preference from client
    if language in ("english", "shona", "ndebele"):
        ctx["language"] = language
    language = ctx["language"]

    try:
        from app.nlp.engine import get_engine
        from app.db import log_exchange

        engine = get_engine()
        intent, confidence = engine.predict_intent(
            message, last_intent=ctx.get("last_intent")
        )

        # Handle language switch
        lang_switch_map = {
            "language_english": "english",
            "language_shona":   "shona",
            "language_ndebele": "ndebele",
        }
        if intent in lang_switch_map:
            language = lang_switch_map[intent]
            ctx["language"] = language

        ctx["last_intent"] = intent
        session.modified   = True

        response_text = (
            engine.get_response(intent, language)
            if intent != "fallback"
            else engine._fallback_response(language)
        )
        response_text = with_safety_notice(response_text)

        # Get localised quick replies for the client
        quick_replies = engine.get_quick_replies(language)

        # Log to Supabase (non-critical)
        try:
            log_exchange(
                phone_number  = f"web:{session_id[:16]}",
                inbound_text  = message,
                outbound_text = response_text,
                intent        = intent,
                channel       = "web",
                language      = language,
            )
        except Exception as e:
            logger.debug(f"Web chat log error: {e}")

        return jsonify({
            "response":      response_text,
            "intent":        intent,
            "confidence":    round(confidence, 3),
            "language":      language,
            "quick_replies": quick_replies,
        })

    except Exception as e:
        logger.error(f"Chat send error: {e}")
        return jsonify({"response": "Sorry, something went wrong. Please try again."}), 500


@dashboard_bp.route("/")
def root():
    if session.get("admin_logged_in"):
        return render_template("dashboard.html")
    return redirect("/chat")


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PAGES — login required
# ══════════════════════════════════════════════════════════════════════════════

@dashboard_bp.route("/admin")
@login_required
def dashboard():
    return render_template("dashboard.html")

@dashboard_bp.route("/api/messages")
@login_required
def page_messages():
    return render_template("messages.html")

@dashboard_bp.route("/api/stats")
@login_required
def page_stats():
    return render_template("stats.html")

@dashboard_bp.route("/api/health")
@login_required
def page_health():
    return render_template("health.html")


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DATA ENDPOINTS — login required
# ══════════════════════════════════════════════════════════════════════════════

@dashboard_bp.route("/api/messages/data")
@login_required
def api_messages_data():
    from app.db import get_messages
    limit    = min(int(request.args.get("limit", 50)), 500)
    intent_f = request.args.get("intent") or None
    dir_f    = request.args.get("direction") or None
    msgs     = get_messages(limit=limit, intent_filter=intent_f, direction_filter=dir_f)
    return jsonify(msgs)


@dashboard_bp.route("/api/stats/data")
@login_required
def api_stats_data():
    from app.db import get_stats
    stats = get_stats()
    stats["training_samples"] = _count_samples()
    stats["intent_count"]     = _count_intents()
    return jsonify(stats)


@dashboard_bp.route("/api/health/data")
@login_required
def api_health_data():
    from app.db import test_connection
    from flask import current_app

    result = {
        "status":           "ok",
        "uptime":           _uptime(),
        "training_samples": _count_samples(),
        "intent_count":     _count_intents(),
        "webhook":          (
            "Twilio signature verification configured"
            if current_app.config.get("TWILIO_AUTH_TOKEN")
            else "Twilio webhook not configured"
        ),
        "scheduler":        "Separate worker process (not monitored)",
        "python_version":   sys.version.split()[0],
        "flask_env":        os.environ.get("FLASK_ENV", "development"),
        "debug":            str(current_app.debug),
        "workers":          "1 (sync/gunicorn)",
        "model_cached":     os.path.exists(MODEL_PATH),
        "database_type":    "Supabase (REST API)",
        "smspop_configured": bool(
            current_app.config.get("SMSPOP_API_TOKEN")
            and current_app.config.get("SMSPOP_SENDER_ID")
        ),
        "sms_delivery_reports_configured": bool(
            current_app.config.get("SMSPOP_DELIVERY_REPORT_URL")
            and current_app.config.get("SMSPOP_WEBHOOK_SECRET")
        ),
        "twilio_whatsapp_configured": all(
            current_app.config.get(name)
            for name in (
                "TWILIO_ACCOUNT_SID",
                "TWILIO_AUTH_TOKEN",
                "TWILIO_WHATSAPP_NUMBER",
                "TWILIO_WHATSAPP_REMINDER_CONTENT_SID",
            )
        ),
        "twilio_webhook_configured": bool(
            current_app.config.get("TWILIO_AUTH_TOKEN")
        ),
    }
    t0 = time.time()
    try:
        from app.nlp.engine import get_engine
        intent, _ = get_engine().predict_intent("hello")
        result["nlp_model"]        = f"OK ({intent})"
        result["response_time_ms"] = round((time.time() - t0) * 1000, 1)
    except Exception as e:
        result["nlp_model"] = "error"
        result["status"]    = "degraded"

    db_ok, db_msg = test_connection()
    result["database"] = db_msg
    result["database_ok"] = db_ok
    if not db_ok:
        result["status"] = "degraded"

    return jsonify(result)