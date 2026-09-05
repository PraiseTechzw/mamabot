"""Transparent, local language detection for MamaBot's three languages."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .preprocessing import normalize_text

SUPPORTED_LANGUAGES = ("en", "sn", "nd")
_LANGUAGE_NAMES = {"en": "English", "sn": "Shona", "nd": "Ndebele"}
_PROFILE_DIR = Path(__file__).resolve().parents[1] / "data" / "language_profiles"
_PROFILE_FILES = {"en": "en.json", "sn": "shona.json", "nd": "ndebele.json"}


@dataclass(frozen=True)
class LanguageProfile:
    code: str
    markers: frozenset[str]
    phrases: tuple[str, ...]
    greetings: frozenset[str]


@dataclass(frozen=True)
class LanguageDetection:
    language: str
    confidence: float
    uncertain: bool
    scores: dict[str, float]
    matched_terms: tuple[str, ...] = ()


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[\w]+(?:'[\w]+)?", text.casefold(), flags=re.UNICODE))


@lru_cache(maxsize=1)
def _profiles() -> dict[str, LanguageProfile]:
    profiles: dict[str, LanguageProfile] = {}
    for code in SUPPORTED_LANGUAGES:
        path = _PROFILE_DIR / _PROFILE_FILES[code]
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = {}
        profiles[code] = LanguageProfile(
            code=code,
            markers=frozenset(str(item).casefold() for item in raw.get("markers", [])),
            phrases=tuple(str(item).casefold() for item in raw.get("phrases", [])),
            greetings=frozenset(
                str(item).casefold() for item in raw.get("greetings", [])
            ),
        )
    return profiles


def detect_language_result(text: str, preferred: str = "en") -> LanguageDetection:
    """Score local profile evidence and retain uncertainty for weak inputs.

    A preferred language is used only as a low-confidence fallback. It is not
    presented as certain evidence, which lets callers decide whether to ask
    for clarification or continue with the user's saved preference.
    """
    preferred = preferred if preferred in SUPPORTED_LANGUAGES else "en"
    normalized = normalize_text(text)
    tokens = set(_tokens(normalized))
    if not tokens:
        return LanguageDetection(
            preferred, 0.0, True, {code: 0.0 for code in SUPPORTED_LANGUAGES}
        )

    scores: dict[str, float] = {}
    matched: dict[str, set[str]] = {}
    for code, profile in _profiles().items():
        terms = tokens & profile.markers
        phrase_hits = {
            phrase for phrase in profile.phrases if phrase in normalized.casefold()
        }
        greeting_hits = tokens & profile.greetings
        scores[code] = len(terms) + len(phrase_hits) * 1.8 + len(greeting_hits) * 1.4
        matched[code] = set(terms) | phrase_hits | greeting_hits

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_language, best_score = ranked[0]
    second_score = ranked[1][1]
    tied = [code for code, score in ranked if score == best_score]
    if len(tied) > 1:
        non_english = [code for code in tied if code != "en"]
        best_language = max(non_english or tied, key=lambda code: len(matched[code]))
    total_evidence = sum(scores.values())
    confidence = (
        min(0.99, best_score / (best_score + second_score + 1.0)) if best_score else 0.0
    )
    uncertain = (
        best_score == 0
        or confidence < 0.58
        or (best_score - second_score < 0.75 and len(tokens) < 5)
    )
    generic_greeting = (
        len(tokens) <= 2 and best_language == "en" and not matched[preferred]
    )
    if generic_greeting and preferred != "en":
        best_language = preferred
        uncertain = True
    if best_score == 0 or (
        uncertain
        and preferred in scores
        and scores[preferred] > 0
        and abs(scores[preferred] - best_score) < 1.0
        and len(tied) == 1
    ):
        best_language = preferred
    return LanguageDetection(
        best_language,
        round(confidence, 3),
        uncertain,
        {
            code: round(score / total_evidence, 3) if total_evidence else 0.0
            for code, score in scores.items()
        },
        tuple(sorted(matched[best_language])),
    )


def detect_language(text: str, default: str = "en") -> str:
    """Backward-compatible language-only API used by existing callers."""
    return detect_language_result(text, default).language


def language_name(code: str) -> str:
    return _LANGUAGE_NAMES.get(code, _LANGUAGE_NAMES["en"])
