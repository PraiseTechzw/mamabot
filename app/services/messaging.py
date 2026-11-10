"""Outbound SMS and WhatsApp integrations."""

from __future__ import annotations

import logging
import hashlib
import hmac
import json
import re
import time
from dataclasses import dataclass
from typing import Any

import requests
from flask import current_app

logger = logging.getLogger(__name__)
SMSPOP_API_URL = "https://smspop.co.zw/api/campaigns"
E164_PATTERN = re.compile(r"^\+[1-9]\d{6,14}$")
SMSPOP_SENDER_PATTERN = re.compile(r"^[A-Za-z0-9]{3,13}$")


class MessagingError(RuntimeError):
    """Raised when a configured messaging provider rejects a send."""


@dataclass(frozen=True)
class SendResult:
    provider: str
    message_id: str | None
    status: str


def validate_phone_number(phone_number: str) -> str:
    if not isinstance(phone_number, str) or not E164_PATTERN.fullmatch(phone_number):
        raise ValueError("phone_number must be an E.164 number, for example +263771234567")
    return phone_number


def send_sms(phone_number: str, message: str, *, campaign_name: str = "MamaBot message") -> SendResult:
    """Send one Zimbabwe SMS using the SMSPoP campaigns API."""
    phone_number = validate_phone_number(phone_number)
    if not phone_number.startswith("+263"):
        raise ValueError("SMSPoP Zimbabwe SMS requires a +263 phone number")
    if not isinstance(message, str) or not message or len(message) > 2000:
        raise ValueError("SMS message must contain between 1 and 2000 characters")
    if not isinstance(campaign_name, str) or not campaign_name.strip():
        raise ValueError("campaign_name must not be empty")

    token = current_app.config.get("SMSPOP_API_TOKEN")
    sender_id = current_app.config.get("SMSPOP_SENDER_ID")
    if not token or not sender_id:
        raise MessagingError("SMSPOP_API_TOKEN and SMSPOP_SENDER_ID must be configured")
    if not SMSPOP_SENDER_PATTERN.fullmatch(sender_id):
        raise ValueError("SMSPOP_SENDER_ID must be 3 to 13 letters or numbers")

    payload: dict[str, Any] = {
        "name": campaign_name[:255],
        "message": message,
        "sender_id": sender_id,
        "contact_import_method": "manual",
        "manual_contacts": phone_number,
    }
    callback_url = current_app.config.get("SMSPOP_DELIVERY_REPORT_URL")
    if callback_url:
        payload["callback_url"] = callback_url

    try:
        response = requests.post(
            SMSPOP_API_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as exc:
        logger.exception("SMSPoP request failed")
        raise MessagingError("SMSPoP request failed") from exc
    except ValueError as exc:
        logger.exception("SMSPoP returned invalid JSON")
        raise MessagingError("SMSPoP returned invalid JSON") from exc

    if not isinstance(result, dict):
        raise MessagingError("SMSPoP returned an invalid response")
    contacts = result.get("data", {}).get("contacts", [])
    if not result.get("success") or not isinstance(contacts, list) or not contacts:
        raise MessagingError("SMSPoP did not accept the message")

    contact = contacts[0]
    if not isinstance(contact, dict):
        raise MessagingError("SMSPoP returned an invalid contact result")
    status = contact.get("status", "unknown")
    if status != "sent":
        reason = contact.get("reason") or status
        raise MessagingError(f"SMSPoP did not accept the message: {reason}")

    return SendResult(
        provider="smspop",
        message_id=str(contact["message_id"]) if contact.get("message_id") is not None else None,
        status="accepted",
    )


def send_whatsapp_reminder(phone_number: str, message: str) -> SendResult:
    """Send a scheduled WhatsApp reminder through an approved Twilio template."""
    phone_number = validate_phone_number(phone_number)
    if not isinstance(message, str) or not message:
        raise ValueError("message must not be empty")

    account_sid = current_app.config.get("TWILIO_ACCOUNT_SID")
    auth_token = current_app.config.get("TWILIO_AUTH_TOKEN")
    sender = current_app.config.get("TWILIO_WHATSAPP_NUMBER")
    content_sid = current_app.config.get("TWILIO_WHATSAPP_REMINDER_CONTENT_SID")
    if not all((account_sid, auth_token, sender, content_sid)):
        raise MessagingError(
            "Twilio credentials, TWILIO_WHATSAPP_NUMBER, and "
            "TWILIO_WHATSAPP_REMINDER_CONTENT_SID must be configured"
        )

    from twilio.rest import Client

    try:
        response = Client(account_sid, auth_token).messages.create(
            from_=sender if sender.startswith("whatsapp:") else f"whatsapp:{sender}",
            to=f"whatsapp:{phone_number}",
            content_sid=content_sid,
            content_variables=json.dumps({"1": message}, ensure_ascii=False),
        )
    except Exception as exc:
        logger.exception("Twilio WhatsApp reminder send failed")
        raise MessagingError("Twilio WhatsApp reminder send failed") from exc

    return SendResult(provider="twilio", message_id=response.sid, status="accepted")


def verify_smspop_signature(
    body: bytes,
    timestamp: str,
    signature: str,
    secret: str,
    *,
    now: float | None = None,
) -> bool:
    if not timestamp.isdigit() or not secret or not signature:
        return False
    current_time = time.time() if now is None else now
    if abs(current_time - int(timestamp)) > 300:
        return False
    digest = hmac.new(
        secret.encode("utf-8"),
        timestamp.encode("ascii") + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={digest}", signature)
