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
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class PregnancyProfile:
    id: int | None
    user_id: int
    last_menstrual_period: date | None = None
    due_date: date | None = None
    gravida: int | None = None
    parity: int | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Appointment:
    id: int | None
    user_id: int
    appointment_date: date
    reminder_sent: bool = False
    appointment_type: str = "anc"
    status: str = "scheduled"
    pregnancy_profile_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class ConversationMessage:
    id: int | None
    user_id: int | None
    channel: str
    direction: str
    text: str
    created_at: datetime | None = None
    conversation_id: int | None = None
    language: str = "en"


@dataclass(frozen=True)
class Conversation:
    id: int | None
    user_id: int | None
    channel: str
    status: str = "open"
    started_at: datetime | None = None
    last_message_at: datetime | None = None


@dataclass(frozen=True)
class Reminder:
    id: int | None
    user_id: int
    scheduled_for: datetime
    appointment_id: int | None = None
    reminder_type: str = "appointment"
    status: str = "pending"
    sent_at: datetime | None = None


@dataclass(frozen=True)
class HealthWorker:
    id: int | None
    name: str
    phone_number: str | None = None
    email: str | None = None
    active: bool = True


@dataclass(frozen=True)
class Escalation:
    id: int | None
    user_id: int
    reason: str
    severity: str = "urgent"
    status: str = "open"
    conversation_id: int | None = None
    assigned_health_worker_id: int | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None
