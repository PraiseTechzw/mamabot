"""Deterministic intent classification for MamaBot's documented scope."""
from __future__ import annotations

import re
from dataclasses import dataclass

INTENTS = (
    "appointment_reminder",
    "danger_sign_query",
    "nutrition_information",
    "language_switch",
    "general_greeting",
    "escalation_to_nurse",
)

_KEYWORDS = {
    "appointment_reminder": {
        "en": {"appointment", "clinic", "visit", "reminder", "schedule", "checkup"},
        "sn": {"musangano", "chipatara", "rangarira", "chiremba"},
        "nd": {"umhlangano", "isibhedlela", "khumbuza", "udokotela"},
    },
    "danger_sign_query": {
        "en": {"danger", "bleeding", "blood", "pain", "headache", "swelling", "fever", "water", "vision", "seizure"},
        "sn": {"zviratidzo", "ropa", "kurwadziwa", "musoro", "kupisa", "mvura", "maziso"},
        "nd": {"izimpawu", "igazi", "ubuhlungu", "ikhanda", "umkhuhlane", "amanzi", "amehlo"},
    },
    "nutrition_information": {
        "en": {"nutrition", "food", "eat", "eating", "diet", "meal", "vitamin", "iron", "drink"},
        "sn": {"zvokudya", "kudya", "chikafu", "vitamini", "simbi", "kunwa"},
        "nd": {"ukudla", "isidlo", "amavitamini", "insimbi", "ukuphuza"},
    },
    "language_switch": {
        "en": {"language", "english", "shona", "ndebele"},
        "sn": {"mutauro", "chirungu", "shona", "ndebele"},
        "nd": {"ulimi", "isingisi", "ishona", "ndebele"},
    },
    "general_greeting": {
        "en": {"hello", "hi", "hey", "good", "morning", "afternoon", "evening"},
        "sn": {"mhoro", "makadini", "mangwanani", "masikati", "manheru"},
        "nd": {"sawubona", "unjani", "ekuseni", "emini", "ntambama"},
    },
    "escalation_to_nurse": {
        "en": {"nurse", "midwife", "help", "emergency", "urgent", "speak", "person", "call"},
        "sn": {"mukoti", "nyamukuta", "ndibatsirei", "chimbichimbi", "taura", "foni"},
        "nd": {"umhlengikazi", "umbelethisi", "ngisize", "okuphuthumayo", "khuluma", "fonela"},
    },
}

_DANGER_TERMS = {"bleeding", "blood", "seizure", "unconscious", "difficulty breathing", "severe pain", "ropa", "kubuda ropa", "igazi", "ukopha"}


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float
    matched_terms: tuple[str, ...]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-ZÀ-ÿ']+", text.lower()))


def classify_intent(text: str, language: str = "en") -> IntentResult:
    tokens = _tokens(text)
    if not tokens:
        return IntentResult("general_greeting", 0.0, ())
    language = language if language in {"en", "sn", "nd"} else "en"
    scores: list[tuple[str, int, tuple[str, ...]]] = []
    for intent in INTENTS:
        terms = _KEYWORDS[intent][language] | _KEYWORDS[intent]["en"]
        matched = tuple(sorted(tokens & terms))
        scores.append((intent, len(matched), matched))
    scores.sort(key=lambda item: (item[1], item[0] == "danger_sign_query"), reverse=True)
    intent, score, matched = scores[0]
    if any(term in text.lower() for term in _DANGER_TERMS):
        intent = "danger_sign_query"
        score = max(score, 2)
        matched = tuple(sorted(set(matched) | {"danger-signal"}))
    confidence = min(0.99, 0.35 + score * 0.18) if score else 0.20
    return IntentResult(intent, confidence, matched)
