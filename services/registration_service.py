"""Registration service: session store + orchestration between DialogueManager
and the multi-step RegistrationHandler.

The ``SessionStore`` is an in-process store keyed by sender identifier.  For a
production system this would be backed by Redis; the threading.Lock here is
sufficient for the single-process Gunicorn worker model described in the README.
"""
from __future__ import annotations

import logging
from threading import Lock

from dialogue.registration import RegistrationHandler
from dialogue.state import ConversationSession, ConversationState

log = logging.getLogger(__name__)


class SessionStore:
    """Thread-safe in-process store for per-sender ConversationSession objects."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}
        self._lock = Lock()

    def get_or_create(self, sender: str) -> ConversationSession:
        with self._lock:
            if sender not in self._sessions:
                self._sessions[sender] = ConversationSession()
            return self._sessions[sender]

    def get(self, sender: str) -> ConversationSession | None:
        return self._sessions.get(sender)

    def clear(self, sender: str) -> None:
        with self._lock:
            self._sessions.pop(sender, None)


class RegistrationService:
    """Coordinates the registration flow for a given transport sender.

    This service is the single entry point used by the dialogue manager and
    the webhook route to check whether a message should enter / continue the
    registration flow.
    """

    def __init__(self, repository: object) -> None:
        self.store = SessionStore()
        self._handler = RegistrationHandler(repository)

    def is_registering(self, sender: str) -> bool:
        session = self.store.get(sender)
        return session is not None and session.is_registering()

    def should_start(self, text: str, sender: str) -> bool:
        session = self.store.get_or_create(sender)
        return self._handler.should_start(text, session)

    def handle(
        self,
        text: str,
        sender: str,
        channel: str = "browser",
        phone_number: str = "",
    ) -> str:
        """Route one inbound message through the registration handler.

        Returns the bot reply text.  Callers do not need to track the session
        state; this service manages it internally.
        """
        # Normalise the phone number: prefer the explicit argument; fall back
        # to the sender identifier if it looks like a phone number.
        from utils.validators import validate_phone_number
        effective_phone = phone_number or sender
        if not validate_phone_number(effective_phone):
            effective_phone = ""

        session = self.store.get_or_create(sender)

        # If idle, start a new registration flow
        if session.state == ConversationState.IDLE:
            reply, done = self._handler.handle(
                text, session, phone_number=effective_phone, channel=channel
            )
        else:
            reply, done = self._handler.handle(
                text, session, phone_number=effective_phone, channel=channel
            )

        if done:
            log.info("Registration flow complete for sender=%s", sender)

        return reply
