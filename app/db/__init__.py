"""
app/db/__init__.py

Supabase via direct REST API — no supabase Python client.
Works on Python 3.14+ because it uses only the requests library.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
def _cfg():
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    return url, key

def _headers():
    _, key = _cfg()
    return {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }

def _ok():
    url, key = _cfg()
    return bool(url and key)

def _url(table):
    url, _ = _cfg()
    return f"{url}/rest/v1/{table}"


# ── Messages ──────────────────────────────────────────────────────────────────

def log_message(phone_number, direction, content,
                intent, channel="whatsapp", language="english"):
    if not _ok():
        return
    try:
        requests.post(
            _url("messages"),
            headers=_headers(),
            json={
                "phone_number": phone_number,
                "direction":    direction,
                "content":      (content or "")[:1000],
                "intent":       intent,
                "channel":      channel,
                "language":     language,
            },
            timeout=5,
        )
    except Exception as e:
        logger.debug(f"log_message failed: {e}")


def log_exchange(phone_number, inbound_text, outbound_text,
                 intent, channel="whatsapp", language="english"):
    log_message(phone_number, "inbound",  inbound_text,  intent, channel, language)
    log_message(phone_number, "outbound", outbound_text, intent, channel, language)


def get_messages(limit=50, intent_filter=None, direction_filter=None):
    if not _ok():
        return []
    try:
        params = {
            "select": "*",
            "order":  "created_at.desc",
            "limit":  limit,
        }
        if intent_filter:
            params["intent"] = f"eq.{intent_filter}"
        if direction_filter:
            params["direction"] = f"eq.{direction_filter}"
        r = requests.get(_url("messages"), headers=_headers(),
                         params=params, timeout=8)
        return r.json() if r.ok else []
    except Exception as e:
        logger.warning(f"get_messages failed: {e}")
        return []


def get_stats():
    empty = {"total_messages": 0, "unique_users": 0, "inbound_count": 0,
             "intent_counts": {}, "language_counts": {}, "recent_fallbacks": []}
    if not _ok():
        return empty
    try:
        # All inbound messages (for counts)
        h = {**_headers(), "Prefer": "count=exact"}
        r_all  = requests.get(_url("messages"),
                              headers={**h}, params={"select": "id", "limit": 1}, timeout=8)
        r_in   = requests.get(_url("messages"),
                              headers={**h},
                              params={"select": "id", "direction": "eq.inbound", "limit": 1},
                              timeout=8)
        total   = int(r_all.headers.get("content-range", "0/0").split("/")[-1]) if r_all.ok else 0
        inbound = int(r_in.headers.get("content-range", "0/0").split("/")[-1]) if r_in.ok else 0

        # Intent + language breakdown
        r_msgs = requests.get(_url("messages"), headers=_headers(),
                              params={"select": "intent,language,phone_number",
                                      "direction": "eq.inbound", "limit": 5000},
                              timeout=10)
        msgs = r_msgs.json() if r_msgs.ok else []
        intent_counts, lang_counts, phones = {}, {}, set()
        for m in msgs:
            i = m.get("intent") or "unknown"
            l = m.get("language") or "english"
            intent_counts[i] = intent_counts.get(i, 0) + 1
            lang_counts[l]   = lang_counts.get(l, 0) + 1
            phones.add(m.get("phone_number", ""))

        # Recent fallbacks
        r_fb = requests.get(_url("messages"), headers=_headers(),
                            params={"select": "*", "intent": "eq.fallback",
                                    "direction": "eq.inbound",
                                    "order": "created_at.desc", "limit": 20},
                            timeout=8)
        fallbacks = r_fb.json() if r_fb.ok else []

        return {
            "total_messages":   total,
            "unique_users":     len(phones),
            "inbound_count":    inbound,
            "intent_counts":    intent_counts,
            "language_counts":  lang_counts,
            "recent_fallbacks": fallbacks,
        }
    except Exception as e:
        logger.warning(f"get_stats failed: {e}")
        return empty


# ── Users ─────────────────────────────────────────────────────────────────────

def get_or_create_user(phone_number, language="english", channel="whatsapp"):
    fallback = {"phone_number": phone_number, "preferred_lang": language,
                "preferred_channel": channel, "last_intent": None}
    if not _ok():
        return fallback
    try:
        r = requests.get(_url("users"), headers=_headers(),
                         params={"phone_number": f"eq.{phone_number}",
                                 "select": "*", "limit": 1},
                         timeout=5)
        if r.ok and r.json():
            return r.json()[0]
        # Create new user
        ins = requests.post(_url("users"), headers=_headers(),
                            json={"phone_number": phone_number,
                                  "preferred_lang": language,
                                  "preferred_channel": channel},
                            timeout=5)
        if ins.ok and ins.json():
            return ins.json()[0]
    except Exception as e:
        logger.debug(f"get_or_create_user failed: {e}")
    return fallback


def update_user_language(phone_number, language):
    if not _ok():
        return
    try:
        requests.patch(
            _url("users"),
            headers=_headers(),
            params={"phone_number": f"eq.{phone_number}"},
            json={"preferred_lang": language},
            timeout=5,
        )
    except Exception as e:
        logger.debug(f"update_user_language failed: {e}")


def update_user_intent(phone_number, intent):
    if not _ok():
        return
    try:
        requests.patch(
            _url("users"),
            headers=_headers(),
            params={"phone_number": f"eq.{phone_number}"},
            json={"last_intent": intent},
            timeout=5,
        )
    except Exception as e:
        logger.debug(f"update_user_intent failed: {e}")


def get_user_language(phone_number):
    if not _ok():
        return "english"
    try:
        r = requests.get(_url("users"), headers=_headers(),
                         params={"phone_number": f"eq.{phone_number}",
                                 "select": "preferred_lang", "limit": 1},
                         timeout=5)
        if r.ok and r.json():
            return r.json()[0].get("preferred_lang", "english")
    except Exception:
        pass
    return "english"


def get_user_last_intent(phone_number):
    if not _ok():
        return None
    try:
        r = requests.get(_url("users"), headers=_headers(),
                         params={"phone_number": f"eq.{phone_number}",
                                 "select": "last_intent", "limit": 1},
                         timeout=5)
        if r.ok and r.json():
            return r.json()[0].get("last_intent")
    except Exception:
        pass
    return None


def get_client():
    """Compatibility shim — used by health check."""
    return True if _ok() else None


def test_connection():
    """Returns (ok: bool, message: str) for health check."""
    if not _ok():
        return False, "SUPABASE_URL or SUPABASE_KEY not set"
    try:
        r = requests.get(
            _url("messages"),
            headers=_headers(),
            params={"select": "id", "limit": 1},
            timeout=5,
        )
        if r.ok:
            return True, "Connected (Supabase REST)"
        return False, f"HTTP {r.status_code}: {r.text[:80]}"
    except Exception as e:
        return False, str(e)[:80]


def _rest_request(method, path, *, params=None, json_body=None, headers=None, timeout=8):
    if not _ok():
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be configured")

    request_headers = _headers()
    if headers:
        request_headers.update(headers)
    response = requests.request(
        method,
        f"{_cfg()[0]}/rest/v1/{path.lstrip('/')}",
        headers=request_headers,
        params=params,
        json=json_body,
        timeout=timeout,
    )
    response.raise_for_status()
    if not response.content:
        return None
    return response.json()


def upsert_patient(patient):
    rows = _rest_request(
        "POST",
        "users",
        params={"on_conflict": "phone_number"},
        json_body=patient,
        headers={"Prefer": "resolution=merge-duplicates,return=representation"},
    )
    if not rows:
        raise RuntimeError("Supabase did not return the saved patient")
    return rows[0]


def get_patient(phone_number):
    rows = _rest_request(
        "GET",
        "users",
        params={
            "select": "phone_number,preferred_lang,due_date,reminders_enabled,consent_at",
            "phone_number": f"eq.{phone_number}",
            "limit": 1,
        },
    )
    return rows[0] if rows else None


def create_appointment(phone_number, appointment_at, clinic_name, idempotency_key):
    rows = _rest_request(
        "POST",
        "appointments",
        params={"on_conflict": "idempotency_key"},
        json_body={
            "phone_number": phone_number,
            "appointment_at": appointment_at.isoformat(),
            "clinic_name": clinic_name,
            "idempotency_key": idempotency_key,
        },
        headers={"Prefer": "resolution=merge-duplicates,return=representation"},
    )
    if not rows:
        raise RuntimeError("Supabase did not return the saved appointment")
    return rows[0]


def create_reminders(reminders):
    if not reminders:
        return []
    rows = _rest_request(
        "POST",
        "reminders",
        params={"on_conflict": "idempotency_key"},
        json_body=reminders,
        headers={"Prefer": "resolution=ignore-duplicates,return=representation"},
    )
    if rows is None:
        raise RuntimeError("Supabase did not return the saved reminders")
    return rows


def claim_due_reminders(limit=50):
    rows = _rest_request(
        "POST",
        "rpc/claim_due_reminders",
        json_body={"p_limit": limit},
        timeout=15,
    )
    return rows or []


def update_reminder(reminder_id, values):
    _rest_request(
        "PATCH",
        "reminders",
        params={"id": f"eq.{reminder_id}"},
        json_body=values,
        headers={"Prefer": "return=minimal"},
    )


def cancel_pending_reminders(phone_number):
    _rest_request(
        "PATCH",
        "reminders",
        params={
            "phone_number": f"eq.{phone_number}",
            "status": "in.(pending,sending)",
        },
        json_body={"status": "cancelled"},
        headers={"Prefer": "return=minimal"},
    )


def save_sms_delivery_report(report):
    _rest_request(
        "POST",
        "sms_delivery_reports",
        params={"on_conflict": "webhook_id"},
        json_body={
            "webhook_id": report["webhook_id"],
            "message_id": report["message_id"],
            "campaign_id": report.get("campaign_id"),
            "phone": report["phone"],
            "network": report.get("network"),
            "status": report["status"],
            "error": report.get("error"),
            "delivered_at": report.get("delivered_at"),
            "payload": report,
        },
        headers={"Prefer": "resolution=ignore-duplicates,return=minimal"},
    )
