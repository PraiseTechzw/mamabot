"""Multi-step registration dialogue handler.

This module owns the entire registration conversation from greeting through
confirmation and persistence.  It is intentionally stateless: all mutable
state lives in a ``ConversationSession`` that callers must supply and persist.

Typical call sequence::

    session = ConversationSession()
    handler = RegistrationHandler(repository)

    # First inbound message triggers the flow
    reply, done = handler.handle("register", session, phone_number="0771234567", channel="sms")
    # done is False while the flow is in progress
    while not done:
        user_text = input()
        reply, done = handler.handle(user_text, session, phone_number="0771234567", channel="sms")
"""
from __future__ import annotations

import logging

from dialogue.state import ConversationSession, ConversationState
from responses.catalog import (
    CHANNEL_LABELS,
    LANGUAGE_LABELS,
    response_for,
)
from utils.validators import (
    normalize_phone_number,
    parse_channel_input,
    parse_language_input,
    validate_due_date,
    validate_name,
    validate_phone_number,
)

log = logging.getLogger(__name__)

# Words that mean "cancel" in any supported language
_CANCEL_WORDS: frozenset[str] = frozenset(
    {"cancel", "stop", "quit", "exit", "kana", "misa", "yima", "hamba"}
)

# Words that mean "yes" or "no" in any supported language
_YES_WORDS: frozenset[str] = frozenset({"yes", "y", "hongu", "yebo", "ehe", "ndio"})
_NO_WORDS: frozenset[str] = frozenset({"no", "n", "aiwa", "cha", "hapana"})

# Fields the user can reference when asking to correct something
_FIELD_ALIASES: dict[str, str] = {
    "name": "name",
    "zita": "name",
    "ibizo": "name",
    "phone": "phone",
    "foni": "phone",
    "ifoni": "phone",
    "number": "phone",
    "nhamba": "phone",
    "inombolo": "phone",
    "language": "language",
    "mutauro": "language",
    "ulimi": "language",
    "due date": "due_date",
    "due": "due_date",
    "date": "due_date",
    "zuva": "due_date",
    "usuku": "due_date",
    "channel": "channel",
    "nzira": "channel",
    "indlela": "channel",
}

# Example future date shown in prompts
_DUE_DATE_EXAMPLE = "2027-03-15"


def _lang(session: ConversationSession) -> str:
    """Return the best language code for prompts given session state."""
    return session.draft.language or "en"


def _is_cancel(text: str) -> bool:
    return text.strip().lower() in _CANCEL_WORDS


def _is_yes(text: str) -> bool:
    return text.strip().lower() in _YES_WORDS


def _is_no(text: str) -> bool:
    return text.strip().lower() in _NO_WORDS


def _channel_label(channel: str, lang: str) -> str:
    labels = CHANNEL_LABELS.get(lang, CHANNEL_LABELS["en"])
    return labels.get(channel, channel.capitalize())


def _language_label(code: str, lang: str) -> str:
    labels = LANGUAGE_LABELS.get(lang, LANGUAGE_LABELS["en"])
    return labels.get(code, code)


class RegistrationHandler:
    """Handles all inbound messages while a registration flow is active.

    The handler is intentionally side-effect-free until the user confirms;
    persistence is deferred to the ``_commit`` step.
    """

    def __init__(self, repository: object) -> None:
        # repository must implement register_user(phone, name, lang, due_date, channel)
        self._repo = repository

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def should_start(self, text: str, session: ConversationSession) -> bool:
        """Return True if *text* should trigger a new registration flow."""
        lower = text.strip().lower()
        keywords = {"register", "registration", "signup", "sign up", "join", "rejistaara", "bhalisa"}
        return session.state == ConversationState.IDLE and any(
            kw in lower for kw in keywords
        )

    def handle(
        self,
        text: str,
        session: ConversationSession,
        phone_number: str = "",
        channel: str = "browser",
    ) -> tuple[str, bool]:
        """Process one inbound message within the registration flow.

        Returns ``(reply_text, flow_complete)``.  When *flow_complete* is True
        the caller may return the session state to ``IDLE``.
        """
        stripped = text.strip()

        # ---- Cancel at any point ----------------------------------------
        if _is_cancel(stripped):
            session.reset()
            lang = session.draft.language or "en"
            return response_for(lang, "reg_cancelled"), True

        # ---- Route by current state -------------------------------------
        state = session.state

        if state == ConversationState.IDLE:
            return self._start(session, phone_number, channel)

        if state == ConversationState.REGISTRATION_NAME:
            return self._collect_name(stripped, session, phone_number, channel)

        if state == ConversationState.REGISTRATION_PHONE:
            return self._collect_phone(stripped, session)

        if state == ConversationState.REGISTRATION_LANGUAGE:
            return self._collect_language(stripped, session, phone_number, channel)

        if state == ConversationState.REGISTRATION_DUE_DATE:
            return self._collect_due_date(stripped, session)

        if state == ConversationState.REGISTRATION_CHANNEL:
            return self._collect_channel(stripped, session)

        if state == ConversationState.REGISTRATION_CONFIRM:
            return self._collect_confirm(stripped, session, phone_number, channel)

        # Unknown state — reset safely
        session.reset()
        return response_for("en", "reg_cancelled"), True

    # ------------------------------------------------------------------
    # Step handlers
    # ------------------------------------------------------------------

    def _start(
        self,
        session: ConversationSession,
        phone_number: str,
        channel: str,
    ) -> tuple[str, bool]:
        """Begin a new registration flow."""
        existing = self._repo.get_user_by_phone(phone_number) if phone_number else None
        if existing and existing.name:
            # User exists; confirm whether they want to update
            lang = existing.language or "en"
            # Pre-fill draft with existing data so they can just confirm
            session.draft.name = existing.name
            session.draft.phone_number = phone_number
            session.draft.language = lang
            if existing.due_date:
                session.draft.due_date = existing.due_date
                session.draft.due_date_raw = str(existing.due_date)
            session.draft.channel = channel
            session.state = ConversationState.REGISTRATION_CONFIRM
            return (
                response_for(lang, "reg_already_registered", name=existing.name),
                False,
            )

        # Fresh registration — pre-fill phone number from transport header if
        # available so we can skip the phone step for WhatsApp / SMS senders.
        if phone_number and validate_phone_number(phone_number):
            session.draft.phone_number = normalize_phone_number(phone_number)

        # Pre-fill channel from the transport layer so we can skip the channel
        # step for channels where the answer is already known (browser, test).
        session.draft.channel = channel

        session.state = ConversationState.REGISTRATION_NAME
        return response_for("en", "reg_welcome"), False

    def _collect_name(
        self,
        text: str,
        session: ConversationSession,
        phone_number: str,
        channel: str,
    ) -> tuple[str, bool]:
        lang = _lang(session)
        if not validate_name(text):
            return response_for(lang, "reg_invalid_name"), False
        session.draft.name = text.strip()

        # If we were correcting a specific field, return to confirmation
        if session.draft.correcting:
            session.draft.correcting = None
            session.state = ConversationState.REGISTRATION_CONFIRM
            return _build_confirm_prompt(session), False

        # If we already have a valid phone from the transport layer, skip that step
        if session.draft.phone_number:
            session.state = ConversationState.REGISTRATION_LANGUAGE
            return response_for(lang, "reg_ask_language"), False

        session.state = ConversationState.REGISTRATION_PHONE
        return response_for(lang, "reg_ask_phone"), False

    def _collect_phone(
        self,
        text: str,
        session: ConversationSession,
    ) -> tuple[str, bool]:
        lang = _lang(session)
        if not validate_phone_number(text):
            return response_for(lang, "reg_invalid_phone"), False
        session.draft.phone_number = normalize_phone_number(text)

        if session.draft.correcting:
            session.draft.correcting = None
            session.state = ConversationState.REGISTRATION_CONFIRM
            return _build_confirm_prompt(session), False

        session.state = ConversationState.REGISTRATION_LANGUAGE
        return response_for(lang, "reg_ask_language"), False

    def _collect_language(
        self,
        text: str,
        session: ConversationSession,
        phone_number: str,
        channel: str,
    ) -> tuple[str, bool]:
        lang = _lang(session)
        chosen = parse_language_input(text)
        if not chosen:
            return response_for(lang, "reg_invalid_language"), False
        session.draft.language = chosen
        new_lang = chosen

        if session.draft.correcting:
            session.draft.correcting = None
            session.state = ConversationState.REGISTRATION_CONFIRM
            return _build_confirm_prompt(session), False

        session.state = ConversationState.REGISTRATION_DUE_DATE
        return response_for(new_lang, "reg_ask_due_date", example=_DUE_DATE_EXAMPLE), False

    def _collect_due_date(
        self,
        text: str,
        session: ConversationSession,
    ) -> tuple[str, bool]:
        lang = _lang(session)
        ok, reason, parsed = validate_due_date(text)
        if not ok:
            return response_for(lang, "reg_invalid_due_date", reason=reason), False
        session.draft.due_date_raw = text.strip()
        session.draft.due_date = parsed

        if session.draft.correcting:
            session.draft.correcting = None
            session.state = ConversationState.REGISTRATION_CONFIRM
            return _build_confirm_prompt(session), False

        # For browser / test channels the channel is already known; skip the step.
        if session.draft.channel in {"browser", "test"}:
            session.state = ConversationState.REGISTRATION_CONFIRM
            return _build_confirm_prompt(session), False

        session.state = ConversationState.REGISTRATION_CHANNEL
        return response_for(lang, "reg_ask_channel"), False

    def _collect_channel(
        self,
        text: str,
        session: ConversationSession,
    ) -> tuple[str, bool]:
        lang = _lang(session)
        chosen = parse_channel_input(text)
        if not chosen:
            return response_for(lang, "reg_invalid_channel"), False
        session.draft.channel = chosen

        if session.draft.correcting:
            session.draft.correcting = None

        session.state = ConversationState.REGISTRATION_CONFIRM
        return _build_confirm_prompt(session), False

    def _collect_confirm(
        self,
        text: str,
        session: ConversationSession,
        phone_number: str,
        channel: str,
    ) -> tuple[str, bool]:
        lang = _lang(session)
        lower = text.strip().lower()

        if _is_yes(lower):
            return self._commit(session)

        if _is_no(lower):
            session.reset()
            return response_for(lang, "reg_cancelled"), True

        # Check if the user named a field to correct
        field = _FIELD_ALIASES.get(lower)
        if field:
            return self._start_correction(field, session)

        # Unrecognised — re-show the confirmation
        return _build_confirm_prompt(session), False

    # ------------------------------------------------------------------
    # Correction flow
    # ------------------------------------------------------------------

    def _start_correction(
        self, field: str, session: ConversationSession
    ) -> tuple[str, bool]:
        lang = _lang(session)
        session.draft.correcting = field

        field_labels: dict[str, str] = {
            "name": {"en": "name", "sn": "zita", "nd": "ibizo"}.get(lang, "name"),
            "phone": {"en": "phone number", "sn": "nhamba yefoni", "nd": "inombolo yefoni"}.get(lang, "phone number"),
            "language": {"en": "language", "sn": "mutauro", "nd": "ulimi"}.get(lang, "language"),
            "due_date": {"en": "expected delivery date", "sn": "zuva rekuzvara", "nd": "usuku lokuzala"}.get(lang, "due date"),
            "channel": {"en": "channel", "sn": "nzira", "nd": "indlela"}.get(lang, "channel"),
        }
        label = field_labels.get(field, field)

        # Transition to the appropriate collection state
        state_map: dict[str, ConversationState] = {
            "name": ConversationState.REGISTRATION_NAME,
            "phone": ConversationState.REGISTRATION_PHONE,
            "language": ConversationState.REGISTRATION_LANGUAGE,
            "due_date": ConversationState.REGISTRATION_DUE_DATE,
            "channel": ConversationState.REGISTRATION_CHANNEL,
        }
        session.state = state_map.get(field, ConversationState.REGISTRATION_CONFIRM)
        return response_for(lang, "reg_correct_prompt", field=label), False

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------

    def _commit(
        self, session: ConversationSession
    ) -> tuple[str, bool]:
        lang = _lang(session)
        draft = session.draft

        # Defensive: ensure we have all required fields
        if not all([draft.name, draft.phone_number, draft.language, draft.due_date, draft.channel]):
            log.warning("Registration commit attempted with incomplete draft: %s", draft)
            return response_for(lang, "reg_error"), False

        try:
            user, _profile = self._repo.register_user(
                phone_number=draft.phone_number,
                name=draft.name,
                language=draft.language,
                due_date=draft.due_date,
                channel=draft.channel,
            )
        except Exception:
            log.exception("Failed to persist registration for %s", draft.phone_number)
            return response_for(lang, "reg_error"), False

        session.state = ConversationState.REGISTERED
        reply = response_for(lang, "reg_complete", name=user.name or draft.name)
        # Reset so the session can be reused for normal dialogue
        session.reset()
        session.state = ConversationState.IDLE
        return reply, True


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _build_confirm_prompt(session: ConversationSession) -> str:
    lang = _lang(session)
    draft = session.draft
    due_str = str(draft.due_date) if draft.due_date else "—"
    channel_label = _channel_label(draft.channel or "—", lang)
    lang_label = _language_label(draft.language or "—", lang)
    return response_for(
        lang,
        "reg_confirm",
        name=draft.name or "—",
        phone=draft.phone_number or "—",
        lang_display=lang_label,
        due_date=due_str,
        channel=channel_label,
    )
