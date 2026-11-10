"""
app/routes/webhook.py
MamaBot — handles:
  1. Twilio WhatsApp  → POST /webhook/twilio
  2. Twilio SMS       → POST /webhook/sms  (international fallback)
  3. Africa's Talking → POST /webhook/at   (Zimbabwe SMS — Econet/NetOne/Telecel)
"""

from flask import Blueprint, current_app, request, Response, jsonify
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
import logging
import os
import requests as http

from app.services.clinical_safety import SAFETY_NOTICE, with_safety_notice

logger     = logging.getLogger(__name__)
webhook_bp = Blueprint("webhook", __name__)

# ── In-memory session fallback ────────────────────────────────────────────────
_mem: dict = {}

def _mem_get(phone):
    if phone not in _mem:
        _mem[phone] = {"language": "english", "last_intent": None}
    return _mem[phone]

def _mem_set(phone, language, last_intent):
    _mem[phone] = {"language": language, "last_intent": last_intent}


# ── SMS response formatter ────────────────────────────────────────────────────
SMS_MAX = 459  # 3 segments, comfortable read on basic phone

def _sms_format(text: str, *, include_safety_notice: bool = False) -> str:
    """Strip markdown, trim to SMS length."""
    text = text.replace("*", "").replace("_", "")
    if include_safety_notice:
        notice_suffix = f"\n\n{SAFETY_NOTICE}"
        budget = SMS_MAX - len(notice_suffix)
        if len(text) > budget:
            truncation_suffix = "\n\nReply 1-7 for topics."
            budget -= len(truncation_suffix)
            trimmed = text[:budget]
            last_nl = trimmed.rfind("\n")
            last_dot = trimmed.rfind(". ")
            cut = max(last_nl, last_dot)
            if cut > budget // 2:
                trimmed = trimmed[:cut]
            return f"{trimmed.strip()}{truncation_suffix}{notice_suffix}"
        return f"{text}{notice_suffix}"

    if len(text) <= SMS_MAX:
        return text
    trimmed  = text[:SMS_MAX]
    last_nl  = trimmed.rfind("\n")
    last_dot = trimmed.rfind(". ")
    cut      = max(last_nl, last_dot)
    if cut > SMS_MAX // 2:
        trimmed = trimmed[:cut]
    return trimmed.strip() + "\n\nReply 1-7 for topics."


# ── Clinic lookup ─────────────────────────────────────────────────────────────
CLINICS = {
    "karoi":          "Karoi District Hospital\n+263 64 2433\nOpen 24hrs",
    "chinhoyi":       "Chinhoyi Provincial Hospital\n+263 67 22448\nOpen 24hrs",
    "harare":         "Parirenyatwa Hospital\n+263 4 794411\n\nSally Mugabe Hospital\n+263 4 621071",
    "bulawayo":       "United Bulawayo Hospitals\n+263 9 72111",
    "mutare":         "Mutare Provincial Hospital\n+263 20 64321",
    "gweru":          "Gweru Provincial Hospital\n+263 54 220206",
    "masvingo":       "Masvingo Provincial Hospital\n+263 39 262323",
    "kwekwe":         "Kwekwe General Hospital\n+263 55 22591",
    "bindura":        "Bindura Provincial Hospital\n+263 71 6461",
    "marondera":      "Marondera General Hospital\n+263 79 23421",
    "chegutu":        "Chegutu District Hospital\n+263 53 2222",
    "zvishavane":     "Zvishavane District Hospital\n+263 51 2700",
    "hwange":         "Hwange Colliery Hospital\n+263 81 22131",
    "victoria falls": "Victoria Falls Hospital\n+263 13 4523",
    "beitbridge":     "Beitbridge District Hospital\n+263 86 2324",
    "rusape":         "Rusape General Hospital\n+263 25 2466",
    "kadoma":         "Kadoma General Hospital\n+263 68 22151",
}
CLINIC_LABEL = {"english":"Nearest Clinic","shona":"Chipatara Chiri Pedyo","ndebele":"Isibhedlela Esiseduze"}

def lookup_clinic(text, language="english"):
    tl = text.lower()
    for district, info in CLINICS.items():
        if district in tl:
            label = CLINIC_LABEL.get(language, "Nearest Clinic")
            return f"{label} - {district.title()}\n\n{info}\n\nCarry your ANC card!"
    return None


# ── Language detection ────────────────────────────────────────────────────────
SHONA_W = {
    "ndiri","ndinoda","ndine","ndinotenda","maita","tatenda","chipatara",
    "mwana","mimba","nhumbu","mushonga","kudya","kurwadziwa","ndabereka",
    "chikafu","kuenda","kubereka","mhoro","makadii","mangwanani","hesi",
}
NDEBELE_W = {
    "ngiyabonga","siyabonga","kulungile","sawubona","sanibonani","ingane",
    "isibhedlela","ukudla","ngibuhlungu","ngikhulelwe","ngizala","lotjhani",
}

def detect_lang(text):
    words = set(text.lower().split())
    s = len(words & SHONA_W)
    n = len(words & NDEBELE_W)
    if s > n and s >= 1: return "shona"
    if n > s and n >= 1: return "ndebele"
    return None


# ── State helpers ─────────────────────────────────────────────────────────────
def get_state(phone):
    try:
        from app.db import get_or_create_user
        u = get_or_create_user(phone)
        if u:
            return {"language": u.get("preferred_lang","english"),
                    "last_intent": u.get("last_intent")}
    except Exception:
        pass
    return _mem_get(phone)

def save_state(phone, language, last_intent):
    _mem_set(phone, language, last_intent)
    try:
        from app.db import update_user_language, update_user_intent
        update_user_language(phone, language)
        update_user_intent(phone, last_intent)
    except Exception:
        pass

def log_db(phone, body, reply, intent, channel, language):
    try:
        from app.db import log_exchange
        log_exchange(phone, body, reply, intent, channel, language)
    except Exception:
        pass


# ── Core NLP processor — shared by all channels ───────────────────────────────
def process_message(body: str, phone: str, channel: str) -> str:
    from app.nlp.engine import get_engine

    LANG_SWITCH = {
        "language_english": "english",
        "language_shona":   "shona",
        "language_ndebele": "ndebele",
    }

    state       = get_state(phone)
    language    = state.get("language", "english")
    last_intent = state.get("last_intent")

    # Auto-detect language from text
    detected = detect_lang(body)
    if detected and detected != language:
        language = detected

    # Clinic lookup bypasses NLP
    clinic = lookup_clinic(body, language)
    if clinic:
        reply = (
            _sms_format(clinic, include_safety_notice=True)
            if channel == "sms"
            else with_safety_notice(clinic)
        )
        save_state(phone, language, "clinic_visits")
        log_db(phone, body, reply, "clinic_visits", channel, language)
        return reply

    # NLP
    engine = get_engine()
    intent, confidence = engine.predict_intent(body, last_intent=last_intent)

    if intent in LANG_SWITCH:
        language = LANG_SWITCH[intent]

    if intent == "fallback":
        reply = engine._fallback_response(language)
    else:
        reply = engine.get_response(intent, language)

    if channel == "sms":
        reply = _sms_format(reply, include_safety_notice=True)
    else:
        reply = with_safety_notice(reply)

    save_state(phone, language, intent)
    log_db(phone, body, reply, intent, channel, language)

    logger.info(f"[{channel.upper()}] intent={intent} lang={language} conf={confidence:.2f}")
    return reply


# ══════════════════════════════════════════════════════════════════════════════
# 1. TWILIO WHATSAPP + TWILIO SMS webhook
# ══════════════════════════════════════════════════════════════════════════════
@webhook_bp.route("/webhook/twilio", methods=["POST"])
@webhook_bp.route("/webhook/sms", methods=["POST"])
@webhook_bp.route("/webhook/whatsapp", methods=["POST"])
def twilio_webhook():
    auth_token = current_app.config.get("TWILIO_AUTH_TOKEN")
    if not auth_token:
        return jsonify({"error": "Twilio webhook authentication is not configured"}), 503

    signature = request.headers.get("X-Twilio-Signature", "")
    base_url = current_app.config.get("TWILIO_WEBHOOK_BASE_URL")
    if base_url:
        public_url = f"{base_url.rstrip('/')}{request.path}"
        if request.query_string:
            public_url = f"{public_url}?{request.query_string.decode('ascii')}"
    else:
        public_url = request.url
    validator = RequestValidator(auth_token)
    if not validator.validate(public_url, request.form, signature):
        return jsonify({"error": "invalid Twilio signature"}), 403

    body    = (request.form.get("Body") or "").strip()
    sender  = request.form.get("From", "unknown")
    channel = "whatsapp" if "whatsapp" in sender.lower() else "sms"

    logger.info(f"[TWILIO-{channel.upper()}] {sender}: {repr(body)}")

    if not body:
        return _twiml("Please send a message. Reply 1-7 to choose a topic.")

    reply = process_message(body, sender, channel)
    return _twiml(reply)


def _twiml(text: str) -> Response:
    resp = MessagingResponse()
    resp.message(text)
    return Response(str(resp), mimetype="application/xml")


# ══════════════════════════════════════════════════════════════════════════════
# 2. AFRICA'S TALKING SMS webhook
# ══════════════════════════════════════════════════════════════════════════════
def at_webhook():
    """
    Africa's Talking sends POST with these fields:
      from    — sender phone number e.g. +263771234567
      to      — your AT number e.g. 12345
      text    — message body
      date    — timestamp
      id      — message ID
    """
    body   = (request.form.get("text") or "").strip()
    sender = (request.form.get("from") or "").strip()
    to     = (request.form.get("to") or "").strip()

    logger.info(f"[AT-SMS] from={sender} to={to}: {repr(body)}")

    if not body or not sender:
        return jsonify({"error": "missing fields"}), 400

    reply = process_message(body, sender, "sms")

    # Send reply via Africa's Talking API
    _at_send(sender, reply, to)

    # AT webhook expects a 200 OK with no body (or empty)
    return Response("", status=200)


def _at_send(to: str, message: str, sender_id: str = None):
    """Send SMS reply via Africa's Talking API."""
    api_key  = os.environ.get("AT_API_KEY", "")
    username = os.environ.get("AT_USERNAME", "")

    if not api_key or not username:
        logger.warning("AT_API_KEY or AT_USERNAME not set")
        return

    # Always use sandbox URL when username is 'sandbox'
    if username.strip().lower() == "sandbox":
        url = "https://api.sandbox.africastalking.com/version1/messaging"
    else:
        url = "https://api.africastalking.com/version1/messaging"

    headers = {
        "apiKey":       api_key,
        "Accept":       "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    payload = {
        "username": username,
        "to":       to,
        "message":  message,
    }

    # Only add 'from' if AT_SENDER_ID is explicitly set
    at_sender = os.environ.get("AT_SENDER_ID", "").strip()
    if at_sender:
        payload["from"] = at_sender

    try:
        r = http.post(url, headers=headers, data=payload, timeout=10)
        logger.info(f"AT reply sent: {r.status_code} — {r.text[:200]}")
        if not r.ok:
            logger.error(f"AT send failed: {r.status_code} {r.text}")
    except Exception as e:
        logger.error(f"AT send exception: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. OUTBOUND SMS sender — for scheduled reminders (used by scheduler)
# ══════════════════════════════════════════════════════════════════════════════
def send_reminder_sms(phone: str, message: str, channel: str = "smspop"):
    """Compatibility wrapper for sending an outbound SMS through SMSPoP."""
    if channel != "smspop":
        raise ValueError("SMS reminders are sent through SMSPoP")
    from app.services.messaging import send_sms

    return send_sms(phone, _sms_format(message))


def _twilio_send(to: str, message: str):
    """Send SMS via Twilio (for international or fallback)."""
    try:
        from twilio.rest import Client
        client = Client(
            os.environ.get("TWILIO_ACCOUNT_SID"),
            os.environ.get("TWILIO_AUTH_TOKEN"),
        )
        client.messages.create(
            body=message,
            from_=os.environ.get("TWILIO_SMS_NUMBER"),
            to=to,
        )
    except Exception as e:
        logger.error(f"Twilio SMS send failed: {e}")


# ── Debug endpoint — visit /webhook/at/test to check AT connection ────────────
def at_test():
    """
    Visit https://mamabot-tl6a.onrender.com/webhook/at/test
    to verify AT credentials and send a test message.
    """
    import os
    api_key  = os.environ.get("AT_API_KEY", "NOT SET")
    username = os.environ.get("AT_USERNAME", "NOT SET")

    # Mask key for security
    masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else api_key

    result = {
        "AT_USERNAME":  username,
        "AT_API_KEY":   masked_key,
        "webhook_url":  "/webhook/at",
        "status":       "credentials loaded" if api_key != "NOT SET" else "MISSING CREDENTIALS"
    }

    # Try a live API check
    try:
        r = http.get(
            "https://api.sandbox.africastalking.com/version1/user",
            headers={"apiKey": api_key, "Accept": "application/json"},
            params={"username": username},
            timeout=5,
        )
        result["api_check"] = f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        result["api_check"] = f"Failed: {e}"

    return jsonify(result)
