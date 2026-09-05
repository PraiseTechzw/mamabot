"""Conversation state machine including multi-step registration flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ConversationState(str, Enum):
    """All valid conversation states for the dialogue manager."""

    # Generic states
    IDLE = "idle"
    ESCALATED = "escalated"
    AWAITING_APPOINTMENT_DATE = "awaiting_appointment_date"

    # Registration flow states (in order)
    REGISTRATION_NAME = "registration_name"
    REGISTRATION_PHONE = "registration_phone"
    REGISTRATION_LANGUAGE = "registration_language"
    REGISTRATION_DUE_DATE = "registration_due_date"
    REGISTRATION_CHANNEL = "registration_channel"
    REGISTRATION_CONFIRM = "registration_confirm"
    REGISTERED = "registered"


# States that belong to the active registration flow
REGISTRATION_STATES: frozenset[ConversationState] = frozenset(
    {
        ConversationState.REGISTRATION_NAME,
        ConversationState.REGISTRATION_PHONE,
        ConversationState.REGISTRATION_LANGUAGE,
        ConversationState.REGISTRATION_DUE_DATE,
        ConversationState.REGISTRATION_CHANNEL,
        ConversationState.REGISTRATION_CONFIRM,
    }
)


@dataclass
class RegistrationDraft:
    """Mutable draft collected during a multi-step registration conversation.

    All fields are optional until the user reaches the confirmation step.
    """

    name: str | None = None
    phone_number: str | None = None
    language: str | None = None  # "en" | "sn" | "nd"
    due_date_raw: str | None = None  # user-supplied raw text, validated later
    due_date: object | None = None  # datetime.date once validated
    channel: str | None = None  # "sms" | "whatsapp" | "browser" | "test"
    # Tracks which field the user last asked to correct
    correcting: str | None = None


@dataclass
class ConversationSession:
    """Per-sender session kept in memory for the duration of a conversation.

    A new session is created the first time a sender contacts the bot and
    persisted in the SessionStore for the lifetime of the process.  For
    production persistence, sessions would be stored in Redis or the DB;
    the in-memory store is sufficient for the current scope.
    """

    state: ConversationState = ConversationState.IDLE
    draft: RegistrationDraft = field(default_factory=RegistrationDraft)

    def is_registering(self) -> bool:
        return self.state in REGISTRATION_STATES

    def reset(self) -> None:
        self.state = ConversationState.IDLE
        self.draft = RegistrationDraft()


@dataclass
class DialogueSession:
    """Small transport-neutral state for non-registration follow-up turns."""

    state: ConversationState = ConversationState.IDLE
    language: str = "en"
    user_id: int | None = None

    def reset(self) -> None:
        self.state = ConversationState.IDLE
