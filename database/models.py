"""Typed domain records used by services and persistence code."""
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class User:
    id: int | None
    phone_number: str
    name: str | None = None
    language: str = "en"
    due_date: date | None = None

@dataclass(frozen=True)
class Appointment:
    id: int | None
    user_id: int
    appointment_date: date
    reminder_sent: bool = False

@dataclass(frozen=True)
class ConversationMessage:
    id: int | None
    user_id: int | None
    channel: str
    direction: str
    text: str
    created_at: datetime | None = None
