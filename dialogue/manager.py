"""Conversation orchestration kept independent from transport providers.

The DialogueManager is the single decision point for inbound messages.  It
checks whether a sender is mid-registration, whether a new registration should
start, and falls back to the NLP pipeline for all other cases.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from database.models import ConversationMessage
from dialogue.escalation import persist_escalation, requires_escalation
from dialogue.state import ConversationState, DialogueSession
from nlp.pipeline import analyze
from responses.catalog import response_for
from services.registration_service import RegistrationService
from utils.dates import parse_iso_date

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class BotReply:
    text: str
    language: str
    intent: str
    confidence: float
    escalation: bool = False


class DialogueManager:
    def __init__(self, repository: object) -> None:
        self.repository = repository
        self._registration = RegistrationService(repository)
        self._sessions: dict[str, DialogueSession] = {}
        self._session_lock = Lock()

    def session_for(self, sender: str) -> DialogueSession:
        with self._session_lock:
            return self._sessions.setdefault(sender, DialogueSession())

    def respond(
        self,
        user_text: str,
        phone_number: str = "local-user",
        preferred_language: str = "en",
        channel: str = "browser",
    ) -> BotReply:
        """Process one inbound message and return a bot reply.

        Registration flow takes precedence over the NLP pipeline; all other
        messages are routed through the NLP intent classifier.
        """
        sender = phone_number  # used as session key
        session = self.session_for(sender)

        # ---- Registration flow ------------------------------------------
        if self._registration.is_registering(sender) or self._registration.should_start(
            user_text, sender
        ):
            reply_text = self._registration.handle(
                user_text,
                sender=sender,
                channel=channel,
                phone_number=phone_number,
            )
            # Persist the exchange in the conversation log
            language = self._registration_language(sender, preferred_language)
            session.language = language
            self._log_exchange(user_text, reply_text, phone_number, channel, language)
            return BotReply(reply_text, language, "registration", 1.0, False)

        # ---- NLP pipeline -----------------------------------------------
        existing_user = self.repository.get_user_by_phone(phone_number)
        effective_language = (
            existing_user.language if existing_user else preferred_language
        )
        analysis = analyze(user_text, effective_language)
        user = self.repository.get_or_create_user(phone_number, analysis.language)
        response_language = analysis.language
        session.language = response_language
        session.user_id = user.id

        if session.state == ConversationState.AWAITING_APPOINTMENT_DATE:
            appointment_date = (
                analysis.entities.appointment_date or analysis.entities.date
            )
            if appointment_date:
                self._save_appointment(phone_number, appointment_date)
                session.reset()
                text = response_for(response_language, "appointment_reminder")
                self._log_exchange(
                    user_text, text, phone_number, channel, response_language, user.id
                )
                return BotReply(
                    text, response_language, "appointment_reminder", 1.0, False
                )

        if analysis.intent.intent == "language_switch" and analysis.entities.language:
            self.repository.update_user_language(
                phone_number, analysis.entities.language
            )
            response_language = analysis.entities.language
            session.language = response_language

        if analysis.intent.intent == "appointment_reminder":
            appointment_date = (
                analysis.entities.appointment_date or analysis.entities.date
            )
            if appointment_date:
                self._save_appointment(phone_number, appointment_date)
            else:
                session.state = ConversationState.AWAITING_APPOINTMENT_DATE

        escalation = analysis.intent.intent in {
            "danger_sign_query",
            "nurse_escalation",
        }
        if requires_escalation(analysis.intent.intent):
            persist_escalation(
                self.repository,
                user.id or 0,
                reason=analysis.text,
            )
        response_intent = (
            "escalation_to_nurse"
            if analysis.intent.intent == "nurse_escalation"
            else analysis.intent.intent
        )
        text = response_for(
            response_language,
            (
                response_intent
                if not analysis.intent.low_confidence
                or analysis.intent.intent == "danger_sign_query"
                else "fallback"
            ),
        )

        self._log_exchange(
            user_text, text, phone_number, channel, response_language, user.id
        )
        return BotReply(
            text,
            response_language,
            analysis.intent.intent,
            analysis.intent.confidence,
            escalation,
        )

    def _registration_language(self, sender: str, fallback: str) -> str:
        registration_session = self._registration.store.get(sender)
        if registration_session and registration_session.draft.language:
            return registration_session.draft.language
        return fallback

    def _save_appointment(self, phone_number: str, value: str) -> None:
        appointment_date = parse_iso_date(value)
        add_appointment = getattr(self.repository, "add_appointment", None)
        if add_appointment is not None:
            add_appointment(phone_number, appointment_date)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log_exchange(
        self,
        inbound: str,
        outbound: str,
        phone_number: str,
        channel: str,
        language: str,
        user_id: int | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        try:
            if user_id is None:
                user = self.repository.get_or_create_user(phone_number, language)
                user_id = user.id
            self.repository.save_message(
                ConversationMessage(None, user_id, channel, "inbound", inbound, now)
            )
            self.repository.save_message(
                ConversationMessage(None, user_id, channel, "outbound", outbound, now)
            )
        except Exception:
            log.exception(
                "Failed to persist conversation messages for %s", phone_number
            )
