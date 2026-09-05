from datetime import date, datetime, timedelta, timezone

from database.queries import InMemoryRepository
from dialogue.manager import DialogueManager


def test_all_six_dialogue_intents_use_shared_manager():
    manager = DialogueManager(InMemoryRepository())
    examples = (
        ("hello", "general_greeting"),
        ("I need nutrition advice", "nutrition_information"),
        ("I have heavy bleeding", "danger_sign_query"),
        ("I need to speak to a nurse", "nurse_escalation"),
        ("change language to Shona", "language_switch"),
    )
    for text, expected in examples:
        reply = manager.respond(text, phone_number=f"user-{expected}", channel="test")
        assert reply.intent == expected
        assert reply.text


def test_appointment_date_is_saved_and_followed_up():
    repository = InMemoryRepository()
    manager = DialogueManager(repository)
    phone = "0771234567"
    appointment_date = (
        datetime.now(timezone.utc).date() + timedelta(days=14)
    ).isoformat()

    first = manager.respond("I need an appointment reminder", phone, channel="test")
    assert first.intent == "appointment_reminder"
    assert manager.session_for(phone).state.value == "awaiting_appointment_date"

    second = manager.respond(
        f"My appointment is on {appointment_date}", phone, channel="test"
    )
    assert second.intent == "appointment_reminder"
    assert repository.appointments[0].appointment_date == date.fromisoformat(
        appointment_date
    )
    assert manager.session_for(phone).state.value == "idle"


def test_danger_and_nurse_messages_create_escalations_without_diagnosis():
    repository = InMemoryRepository()
    manager = DialogueManager(repository)

    danger = manager.respond("I have heavy bleeding", "0771234567", channel="test")
    nurse = manager.respond("I need to speak to a nurse", "0771234567", channel="test")

    assert danger.escalation is True
    assert nurse.escalation is True
    assert len(repository.escalations) == 2
    assert "diagnos" in danger.text.lower() or "urgent" in danger.text.lower()


def test_returning_user_language_preference_is_used():
    repository = InMemoryRepository()
    manager = DialogueManager(repository)
    phone = "0771234567"

    manager.respond("change language to Shona", phone, channel="test")
    reply = manager.respond("hello", phone, channel="test")

    assert repository.get_or_create_user(phone).language == "sn"
    assert reply.language == "sn"
