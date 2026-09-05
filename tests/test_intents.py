from nlp.intent_classifier import INTENTS, classify_intent, load_model
from nlp.pipeline import analyze


def test_trained_model_classifies_all_required_intents():
    examples = {
        "appointment_reminder": "Please remind me about my next clinic appointment",
        "danger_sign_query": "I have heavy bleeding and severe pain",
        "nutrition_information": "What nutritious food should I eat during pregnancy?",
        "language_switch": "Please change my language to Shona",
        "general_greeting": "Hello MamaBot",
        "nurse_escalation": "I need to speak to a nurse urgently",
    }
    for expected, text in examples.items():
        result = classify_intent(text)
        assert result.intent == expected
        assert 0.0 <= result.confidence <= 1.0


def test_multilingual_intents_are_supported():
    examples = (
        ("Ndibatsirei kuyeuka musangano wechipatara", "appointment_reminder"),
        ("Ngopha kakhulu ngesikhathi sokukhulelwa", "danger_sign_query"),
        ("Kuyini ukudla okuhle ngesikhathi sokukhulelwa?", "nutrition_information"),
        ("Guqula ulimi lube isiNdebele", "language_switch"),
        ("Sawubona MamaBot", "general_greeting"),
        ("Ngifuna ukukhuluma lomhlengikazi", "nurse_escalation"),
    )
    for text, expected in examples:
        assert classify_intent(text).intent == expected


def test_unknown_message_returns_probability_for_safe_fallback():
    result = classify_intent("qwerty asdf zxcv")
    assert result.intent in INTENTS
    assert result.confidence < 0.45
    assert result.low_confidence is True


def test_danger_signs_are_an_intent_not_a_diagnosis():
    result = classify_intent("I am bleeding and have severe abdominal pain")
    assert result.intent == "danger_sign_query"
    assert "diagnos" not in result.intent.lower()


def test_pipeline_passes_detected_language_to_intent_classifier():
    analysis = analyze("Ndiri kubuda ropa zvakanyanya")
    assert analysis.language == "sn"
    assert analysis.intent.intent == "danger_sign_query"


def test_runtime_loads_saved_model_artifact():
    model = load_model()
    assert set(model.named_steps["classifier"].classes_) == set(INTENTS)
