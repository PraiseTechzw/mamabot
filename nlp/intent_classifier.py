"""Trainable local intent classifier for MamaBot.

The model uses word and character TF-IDF features with logistic regression.
This is deterministic, lightweight enough for local Flask use, and supports
probability-based low-confidence handling without a hosted API.
"""

from __future__ import annotations

import json
import os
import pickle
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from .preprocessing import normalize_text

INTENTS = (
    "appointment_reminder",
    "danger_sign_query",
    "nutrition_information",
    "language_switch",
    "general_greeting",
    "nurse_escalation",
)
DEFAULT_CONFIDENCE_THRESHOLD = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.45"))
ROOT = Path(__file__).resolve().parents[1]
TRAINING_PATH = ROOT / "data" / "corpus" / "training.json"
MODEL_PATH = ROOT / "models" / "intent" / "model.pkl"


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float
    matched_terms: tuple[str, ...] = ()
    low_confidence: bool = False


def load_corpus(path: Path = TRAINING_PATH) -> list[dict[str, str]]:
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError(f"Corpus must be a non-empty list: {path}")
    valid: list[dict[str, str]] = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("text"), str):
            raise TypeError(f"Invalid corpus record: {record!r}")
        if record.get("intent") not in INTENTS:
            raise ValueError(f"Unsupported intent in corpus: {record.get('intent')!r}")
        valid.append(
            {"text": normalize_text(record["text"]), "intent": record["intent"]}
        )
    return valid


def build_model(records: list[dict[str, str]] | None = None) -> Pipeline:
    records = records or load_corpus()
    texts = [record["text"] for record in records]
    labels = [record["intent"] for record in records]
    features = FeatureUnion(
        [
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True
                ),
            ),
        ]
    )
    model = Pipeline(
        [
            ("features", features),
            (
                "classifier",
                LogisticRegression(max_iter=1500, random_state=42, solver="lbfgs"),
            ),
        ]
    )
    model.fit(texts, labels)
    return model


def save_model(model: Pipeline, path: Path = MODEL_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as artifact:
        pickle.dump(model, artifact, protocol=pickle.HIGHEST_PROTOCOL)


@lru_cache(maxsize=4)
def load_model(path: Path = MODEL_PATH) -> Pipeline:
    if not path.exists():
        model = build_model()
        save_model(model, path)
        return model
    try:
        with path.open("rb") as artifact:
            model = pickle.load(artifact)
    except (AttributeError, EOFError, OSError, pickle.UnpicklingError, ValueError):
        model = build_model()
        save_model(model, path)
    if not isinstance(model, Pipeline) or not hasattr(model, "predict_proba"):
        raise ValueError(f"Invalid intent model artifact: {path}")
    return model


def _model_classes(model: Pipeline) -> tuple[str, ...]:
    classifier: Any = model.named_steps["classifier"]
    return tuple(str(label) for label in classifier.classes_)


def classify_intent(
    text: str,
    language: str = "en",
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    model: Pipeline | None = None,
) -> IntentResult:
    """Classify a normalized message and return its probability confidence.

    Low-confidence results retain the model's best intent and low probability;
    the dialogue layer can use the threshold to select a safe fallback. No
    intent represents a diagnosis: danger signs are classified as a safety
    conversation category for urgent guidance/escalation.
    """
    del language  # Language is represented by the multilingual training text.
    normalized = normalize_text(text)
    if not normalized:
        return IntentResult("general_greeting", 0.0, low_confidence=True)
    classifier = model or load_model()
    probabilities = classifier.predict_proba([normalized])[0]
    classes = _model_classes(classifier)
    best_index = max(range(len(probabilities)), key=probabilities.__getitem__)
    intent = classes[best_index]
    confidence = float(probabilities[best_index])
    return IntentResult(
        intent, round(confidence, 3), low_confidence=confidence < threshold
    )
