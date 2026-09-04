from datetime import date

import pytest

from app import create_app
from database.queries import InMemoryRepository
from dialogue.manager import DialogueManager
from messaging.test_provider import TestMessageProvider
from nlp.intent_classifier import INTENTS, classify_intent
from nlp.language_detector import detect_language
from reminders.anc_reminders import send_due_reminders
from utils.validators import validate_message, validate_phone_number


def test_supported_languages_are_detected():
    assert detect_language("Hello, I need an appointment") == "en"
    assert detect_language("Mangwanani, ndiri kunzwa kurwadziwa") == "sn"
    assert detect_language("Sawubona ngikhulelwe") == "nd"


def test_all_documented_intents_are_reachable():
    examples = {
        "appointment_reminder": "I need an appointment reminder",
        "danger_sign_query": "I have bleeding and severe pain",
        "nutrition_information": "What food should I eat for nutrition",
        "language_switch": "change language to Shona",
        "general_greeting": "hello",
        "escalation_to_nurse": "I need to speak to a nurse",
    }
    assert {classify_intent(text).intent for text in examples.values()} == set(INTENTS)


def test_danger_signs_escalate_without_diagnosis():
    manager = DialogueManager(InMemoryRepository())
    reply = manager.respond("I have heavy bleeding", channel="test")
    assert reply.escalation is True
    assert "cannot diagnose" in reply.text.lower()
    assert "urgent" in reply.text.lower()


def test_validation_rejects_empty_or_oversized_messages():
    with pytest.raises(ValueError):
        validate_message(" ")
    with pytest.raises(ValueError):
        validate_message("x" * 1001)
    assert validate_phone_number("0771234567")
    assert not validate_phone_number("123")


def test_local_flask_chat_works_without_external_credentials():
    client = create_app({"TESTING": True}).test_client()
    response = client.post("/api/chat", json={"message": "Hello MamaBot"})
    assert response.status_code == 200
    assert response.get_json()["intent"] == "general_greeting"
    assert client.get("/").status_code == 200


def test_reminder_job_sends_once():
    repository = InMemoryRepository()
    repository.add_appointment("0771234567", date(2026, 9, 4))
    provider = TestMessageProvider()
    assert send_due_reminders(provider, date(2026, 9, 4), repository) == 1
    assert send_due_reminders(provider, date(2026, 9, 4), repository) == 0
    assert len(provider.sent) == 1
