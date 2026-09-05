"""Input validation and normalization."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone


def validate_phone_number(value: str) -> bool:
    """Accept Zimbabwe mobile numbers: +2637xxxxxxxx or 07xxxxxxxx."""
    return bool(re.fullmatch(r"(?:\+263|0)7\d{8}", value.strip()))


def normalize_phone_number(value: str) -> str:
    """Normalize to +263 international format."""
    value = value.strip()
    if value.startswith("0"):
        return "+263" + value[1:]
    return value


def validate_name(value: str) -> bool:
    """At least two characters, no purely numeric strings."""
    stripped = value.strip()
    return len(stripped) >= 2 and not stripped.isdigit()


def validate_language(value: str) -> bool:
    return value.strip().lower() in {"en", "sn", "nd"}


LANGUAGE_ALIASES: dict[str, str] = {
    # English
    "en": "en", "english": "en", "chirungu": "en", "isingisi": "en",
    # Shona
    "sn": "sn", "shona": "sn", "chiShona": "sn", "chishona": "sn",
    # Ndebele
    "nd": "nd", "ndebele": "nd", "isindebele": "nd", "sindebele": "nd",
}

CHANNEL_ALIASES: dict[str, str] = {
    "sms": "sms",
    "whatsapp": "whatsapp",
    "1": "sms",
    "2": "whatsapp",
    "3": "browser",
    "browser": "browser",
    "test": "test",
}

SUPPORTED_CHANNELS = frozenset({"sms", "whatsapp", "browser", "test"})


def parse_language_input(value: str) -> str | None:
    """Return a normalised language code or None if unrecognised."""
    key = value.strip().lower()
    return LANGUAGE_ALIASES.get(key)


def parse_channel_input(value: str) -> str | None:
    """Return a normalised channel code or None if unrecognised."""
    key = value.strip().lower()
    return CHANNEL_ALIASES.get(key)


def validate_due_date(value: str) -> tuple[bool, str, date | None]:
    """Parse and sanity-check an expected delivery date.

    Returns (ok, error_message, parsed_date).  Dates must be in the future
    and within 42 weeks (normal pregnancy window from today).
    """
    from utils.dates import parse_iso_date

    try:
        parsed = parse_iso_date(value.strip())
    except ValueError:
        return False, "date must use YYYY-MM-DD format (e.g. 2026-12-15)", None

    today = datetime.now(tz=timezone.utc).date()
    if parsed <= today:
        return False, "the expected delivery date must be in the future", None
    max_future = datetime.now(tz=timezone.utc).date() + timedelta(weeks=42)
    if parsed > max_future:
        return False, "the expected delivery date seems too far away — please check the date", None
    return True, "", parsed


def validate_message(value: object, maximum: int = 1000) -> str:
    if not isinstance(value, str):
        raise TypeError("message must be a string")
    value = value.strip()
    if not value:
        raise ValueError("message cannot be empty")
    if len(value) > maximum:
        raise ValueError(f"message exceeds {maximum} characters")
    return value
