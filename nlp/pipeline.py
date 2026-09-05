"""End-to-end local NLP pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from .entity_extractor import Entities, extract_entities
from .intent_classifier import IntentResult, classify_intent
from .language_detector import detect_language_result
from .preprocessing import normalize_text


@dataclass(frozen=True)
class Analysis:
    text: str
    language: str
    intent: IntentResult
    entities: Entities
    language_confidence: float = 0.0
    language_uncertain: bool = True


def analyze(text: str, preferred_language: str = "en") -> Analysis:
    normalized = normalize_text(text)
    detection = detect_language_result(normalized, preferred_language)
    return Analysis(
        normalized,
        detection.language,
        classify_intent(normalized, detection.language),
        extract_entities(normalized),
        detection.confidence,
        detection.uncertain,
    )
