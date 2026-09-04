"""End-to-end local NLP pipeline."""
from __future__ import annotations

from dataclasses import dataclass

from .entity_extractor import Entities, extract_entities
from .intent_classifier import IntentResult, classify_intent
from .language_detector import detect_language
from .preprocessing import normalize_text


@dataclass(frozen=True)
class Analysis:
    text: str
    language: str
    intent: IntentResult
    entities: Entities

def analyze(text: str, preferred_language: str = "en") -> Analysis:
    normalized = normalize_text(text)
    language = detect_language(normalized, preferred_language)
    return Analysis(normalized, language, classify_intent(normalized, language), extract_entities(normalized))
