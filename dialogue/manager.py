"""Conversation orchestration kept independent from transport providers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from database.models import ConversationMessage
from database.queries import InMemoryRepository
from nlp.pipeline import analyze
from responses.catalog import response_for


@dataclass(frozen=True)
class BotReply:
    text: str
    language: str
    intent: str
    confidence: float
    escalation: bool = False

class DialogueManager:
    def __init__(self, repository: InMemoryRepository): self.repository = repository
    def respond(self, user_text: str, phone_number: str = "local-user", preferred_language: str = "en", channel: str = "browser") -> BotReply:
        analysis = analyze(user_text, preferred_language)
        user = self.repository.get_or_create_user(phone_number, analysis.language)
        if analysis.intent.intent == "language_switch" and analysis.entities.language:
            self.repository.update_user_language(phone_number, analysis.entities.language)
        escalation = analysis.intent.intent in {"danger_sign_query", "escalation_to_nurse"}
        text = response_for(analysis.language, analysis.intent.intent if analysis.intent.confidence >= 0.40 else "fallback")
        self.repository.save_message(ConversationMessage(None, user.id, channel, "inbound", analysis.text, datetime.now(timezone.utc)))
        self.repository.save_message(ConversationMessage(None, user.id, channel, "outbound", text, datetime.now(timezone.utc)))
        return BotReply(text, analysis.language, analysis.intent.intent, analysis.intent.confidence, escalation)
