"""Conversation orchestration kept independent from transport providers.

The DialogueManager is the single decision point for inbound messages.  It
checks whether a sender is mid-registration, whether a new registration should
start, and falls back to the NLP pipeline for all other cases.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from database.models import ConversationMessage
from nlp.pipeline import analyze
from responses.catalog import response_for
from services.registration_service import RegistrationService

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
            self._log_exchange(user_text, reply_text, phone_number, channel, "en")
            return BotReply(reply_text, "en", "registration", 1.0, False)

        # ---- NLP pipeline -----------------------------------------------
        analysis = analyze(user_text, preferred_language)
        user = self.repository.get_or_create_user(phone_number, analysis.language)
        response_language = analysis.language

        if analysis.intent.intent == "language_switch" and analysis.entities.language:
            self.repository.update_user_language(
                phone_number, analysis.entities.language
            )
            response_language = analysis.entities.language

        escalation = analysis.intent.intent in {
            "danger_sign_query",
            "escalation_to_nurse",
        }
        text = response_for(
            response_language,
            (
                analysis.intent.intent
                if analysis.intent.confidence >= 0.40
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
