"""Scheduling helpers for opt-in WhatsApp reminders."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from app import db
from app.services.messaging import validate_phone_number

HARARE = ZoneInfo("Africa/Harare")


def _idempotency_key(phone_number: str, kind: str, scheduled_at: datetime) -> str:
    identity = f"{phone_number}:{kind}:{scheduled_at.isoformat()}"
    return str(uuid5(NAMESPACE_URL, identity))


def _parse_aware_datetime(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("date/time must be an ISO 8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("date/time must be an ISO 8601 string") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=HARARE)
    return parsed.astimezone(timezone.utc)


def _require_reminder_consent(phone_number: str) -> dict:
    validate_phone_number(phone_number)
    patient = db.get_patient(phone_number)
    if not patient:
        raise ValueError("Patient is not registered")
    if not patient.get("reminders_enabled") or not patient.get("consent_at"):
        raise PermissionError("Recorded reminder consent is required")
    return patient


def _reminder(phone_number: str, category: str, content: str, scheduled_at: datetime) -> dict:
    return {
        "phone_number": phone_number,
        "category": category,
        "channel": "whatsapp",
        "content": content,
        "scheduled_at": scheduled_at.isoformat(),
        "idempotency_key": _idempotency_key(phone_number, category, scheduled_at),
    }


def schedule_reminder(
    phone_number: str,
    content: str,
    scheduled_at: str,
    category: str = "general",
) -> dict:
    if category not in {"weekly_pregnancy", "anc_appointment", "general"}:
        raise ValueError("Unsupported reminder category")
    if not content or len(content) > 2000:
        raise ValueError("content must contain between 1 and 2000 characters")
    _require_reminder_consent(phone_number)
    scheduled = _parse_aware_datetime(scheduled_at)
    if scheduled <= datetime.now(timezone.utc):
        raise ValueError("scheduled_at must be in the future")
    return db.create_reminders([_reminder(phone_number, category, content, scheduled)])[0]


def schedule_appointment_reminders(
    phone_number: str,
    appointment_at: str,
    content: str,
    clinic_name: str | None = None,
) -> dict:
    if not content or len(content) > 2000:
        raise ValueError("content must contain between 1 and 2000 characters")
    _require_reminder_consent(phone_number)
    appointment = _parse_aware_datetime(appointment_at)
    now = datetime.now(timezone.utc)
    if appointment <= now:
        raise ValueError("appointment_at must be in the future")

    reminders = [
        _reminder(phone_number, "anc_appointment", content, appointment - timedelta(days=days))
        for days in (7, 1)
        if appointment - timedelta(days=days) > now
    ]
    if not reminders:
        raise ValueError("Appointment is too soon to schedule a reminder")

    appointment_record = db.create_appointment(
        phone_number,
        appointment,
        clinic_name,
        _idempotency_key(phone_number, "appointment", appointment),
    )
    for reminder in reminders:
        reminder["appointment_id"] = appointment_record["id"]
    appointment_record["reminders"] = db.create_reminders(reminders)
    return appointment_record


def schedule_weekly_pregnancy_reminders(
    phone_number: str,
    messages: list[str],
) -> list[dict]:
    if not isinstance(messages, list) or not messages or len(messages) > 52:
        raise ValueError("messages must contain 1 to 52 weekly messages")
    if any(not isinstance(message, str) or not message.strip() or len(message) > 2000 for message in messages):
        raise ValueError("Each weekly message must contain between 1 and 2000 characters")

    patient = _require_reminder_consent(phone_number)
    due_date_value = patient.get("due_date")
    if not due_date_value:
        raise ValueError("A due_date must be recorded before scheduling weekly reminders")
    due_date = date.fromisoformat(due_date_value[:10])

    now_local = datetime.now(HARARE)
    days_until_wednesday = (2 - now_local.weekday()) % 7
    next_send = datetime.combine(
        now_local.date() + timedelta(days=days_until_wednesday),
        time(hour=10),
        tzinfo=HARARE,
    )
    if next_send <= now_local:
        next_send += timedelta(days=7)

    dates: list[datetime] = []
    while next_send.date() <= due_date:
        dates.append(next_send.astimezone(timezone.utc))
        next_send += timedelta(days=7)
    if len(dates) != len(messages):
        raise ValueError(
            f"Provide exactly {len(dates)} messages for the upcoming Wednesdays before the due date"
        )

    reminders = [
        _reminder(phone_number, "weekly_pregnancy", message.strip(), scheduled_at)
        for message, scheduled_at in zip(messages, dates)
    ]
    return db.create_reminders(reminders)
