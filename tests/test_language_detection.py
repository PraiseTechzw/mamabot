from database.queries import InMemoryRepository
from dialogue.manager import DialogueManager
from nlp.language_detector import detect_language_result
from nlp.pipeline import analyze
from nlp.preprocessing import normalize_text


def test_representative_utterances_are_detected():
    examples = {
        "en": "Hello, I need an appointment reminder",
        "sn": "Mangwanani, ndiri kunzwa kurwadziwa",
        "nd": "Sawubona ngikhulelwe futhi ngizwa ubuhlungu",
    }
    for language, text in examples.items():
        result = detect_language_result(text)
        assert result.language == language
        assert result.confidence > 0.5
        assert result.uncertain is False


def test_normalization_handles_unicode_spacing_and_control_characters():
    assert normalize_text("  Sawubona\n\tngikhulelwe  ") == "Sawubona ngikhulelwe"
    assert normalize_text("Ｍａｋａｄｉｎｉ") == "Makadini"


def test_unknown_text_keeps_preference_but_is_marked_uncertain():
    result = detect_language_result("qwerty asdf", preferred="sn")
    assert result.language == "sn"
    assert result.confidence == 0.0
    assert result.uncertain is True


def test_code_switching_prefers_distinctive_local_evidence():
    result = detect_language_result("hello makadini appointment musangano")
    assert result.language == "sn"
    assert result.uncertain is True


def test_pipeline_exposes_language_confidence_separately_from_intent():
    analysis = analyze("Sawubona ngikhulelwe")
    assert analysis.language == "nd"
    assert analysis.language_confidence > 0.5
    assert analysis.intent.intent != "language_switch"


def test_explicit_language_switch_updates_user_and_reply_language():
    repository = InMemoryRepository()
    manager = DialogueManager(repository)

    reply = manager.respond("change language to Shona", "0771234567")

    assert reply.language == "sn"
    assert repository.get_or_create_user("0771234567").language == "sn"
