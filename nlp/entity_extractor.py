"""Local entity extraction for MamaBot registration and appointment workflows."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from utils.validators import (
    normalize_phone_number,
    parse_language_input,
    validate_name,
    validate_phone_number,
)

from .preprocessing import normalize_text

ROOT = Path(__file__).resolve().parents[1]
PATTERN_PATH = ROOT / "models" / "ner" / "patterns.json"
_DATE_PATTERN = re.compile(
    r"\b(?:20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2}|\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+20\d{2})\b",
    re.IGNORECASE,
)
_DUE_MARKERS = (
    "due date",
    "delivery date",
    "expected delivery",
    "zuva rekuzvara",
    "usuku lokuzala",
)
_APPOINTMENT_MARKERS = (
    "appointment",
    "clinic",
    "visit",
    "checkup",
    "musangano",
    "kiriniki",
    "umhlangano",
    "umtholampilo",
)


@dataclass(frozen=True)
class Entities:
    person_name: str | None = None
    phone_number: str | None = None
    date: str | None = None
    due_date: str | None = None
    appointment_date: str | None = None
    language: str | None = None


@lru_cache(maxsize=1)
def _entity_ruler():
    try:
        import spacy

        nlp = spacy.blank("xx")
        ruler = nlp.add_pipe("entity_ruler", config={"phrase_matcher_attr": "LOWER"})
        patterns = json.loads(PATTERN_PATH.read_text(encoding="utf-8"))
        ruler.add_patterns(patterns)
        return nlp
    except (ImportError, OSError, json.JSONDecodeError, ValueError):
        return None


def _parse_date(value: str) -> str | None:
    cleaned = value.strip().replace("/", "-")
    formats = ("%Y-%m-%d", "%d-%m-%Y", "%d %B %Y", "%d %b %Y")
    for fmt in formats:
        try:
            return (
                datetime.strptime(cleaned, fmt)
                .replace(tzinfo=timezone.utc)
                .date()
                .isoformat()
            )
        except ValueError:
            continue
    return None


def _extract_date(text: str) -> str | None:
    for match in _DATE_PATTERN.finditer(text):
        parsed = _parse_date(match.group(0))
        if parsed:
            return parsed
    return None


def _extract_person(text: str) -> str | None:
    document = _entity_ruler()(text) if _entity_ruler() else None
    if document:
        for entity in document.ents:
            if entity.label_ == "PERSON" and validate_name(entity.text.split()[-1]):
                return entity.text.split()[-1].strip(".,")
    patterns = (
        r"\bmy name is\s+([\w'\-]+(?:\s+[\w'\-]+)?)",
        r"\bzita rangu ndi\s*([\w'\-]+)",
        r"\bndinonzi\s*([\w'\-]+)",
        r"\bibizo lami ngu\s*([\w'\-]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and validate_name(match.group(1)):
            return match.group(1).strip(".,")
    return None


def _extract_language(text: str) -> str | None:
    document = _entity_ruler()(text) if _entity_ruler() else None
    if document:
        for entity in document.ents:
            if entity.label_ == "LANGUAGE":
                language = parse_language_input(entity.text)
                if language:
                    return language
    for alias in ("english", "chirungu", "shona", "chishona", "ndebele", "isindebele"):
        if re.search(rf"\b{re.escape(alias)}\b", text, re.IGNORECASE):
            return parse_language_input(alias)
    return None


def extract_entities(text: str) -> Entities:
    """Extract only workflow entities and return safe normalized values."""
    normalized = normalize_text(text)
    lowered = normalized.casefold()
    phone_match = re.search(r"(?:\+263|0)7\d{8}", normalized)
    phone = (
        phone_match.group(0)
        if phone_match and validate_phone_number(phone_match.group(0))
        else None
    )
    phone = normalize_phone_number(phone) if phone else None
    extracted_date = _extract_date(normalized)
    due_date = (
        extracted_date if any(marker in lowered for marker in _DUE_MARKERS) else None
    )
    appointment_date = (
        extracted_date
        if any(marker in lowered for marker in _APPOINTMENT_MARKERS)
        else None
    )
    return Entities(
        person_name=_extract_person(normalized),
        phone_number=phone,
        date=extracted_date,
        due_date=due_date,
        appointment_date=appointment_date,
        language=_extract_language(normalized),
    )
