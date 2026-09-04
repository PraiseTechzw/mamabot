"""Language detection for MamaBot's supported languages.

The detector intentionally uses transparent lexical signals so local tests and
local browser chat work without a hosted model or paid API.
"""
from __future__ import annotations

import re
from collections import Counter

SUPPORTED_LANGUAGES = ("en", "sn", "nd")
_LANGUAGE_NAMES = {"en": "English", "sn": "Shona", "nd": "Ndebele"}

_MARKERS = {
    "sn": {"mangwanani", "makadini", "ndiri", "zvokudya", "nhumbu", "mai", "zviratidzo", "kurwadziwa", "ndibatsirei", "chiremba", "musangano"},
    "nd": {"sawubona", "unjani", "ngikhulelwe", "ukudla", "izimpawu", "ubuhlungu", "ngisize", "umhlengikazi", "isibhedlela", "umhlangano"},
    "en": {"hello", "hi", "pregnant", "food", "nutrition", "danger", "pain", "help", "nurse", "hospital", "appointment", "reminder"},
}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-ZÀ-ÿ']+", text.lower()))


def detect_language(text: str, default: str = "en") -> str:
    """Return an ISO-like supported language code.

    Unknown or empty messages use the caller's supported default, which is
    English unless explicitly overridden with ``sn`` or ``nd``.
    """
    if default not in SUPPORTED_LANGUAGES:
        default = "en"
    tokens = _tokens(text)
    if not tokens:
        return default
    scores = Counter({language: len(tokens & markers) for language, markers in _MARKERS.items()})
    best_language, best_score = scores.most_common(1)[0]
    return best_language if best_score else default


def language_name(code: str) -> str:
    return _LANGUAGE_NAMES.get(code, _LANGUAGE_NAMES["en"])
