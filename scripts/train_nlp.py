"""Train and evaluate MamaBot's reproducible local intent model."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nlp.intent_classifier import (
    INTENTS,
    MODEL_PATH,
    build_model,
    load_corpus,
    save_model,
)

VALIDATION_PATH = ROOT / "data" / "corpus" / "validation.json"
TEST_PATH = ROOT / "data" / "corpus" / "test.json"


def _load_split(path: Path) -> list[dict[str, str]]:
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError(f"Corpus must be a non-empty list: {path}")
    return records


def _assert_no_leakage(
    train: list[dict[str, str]],
    validation: list[dict[str, str]],
    test: list[dict[str, str]],
) -> None:
    sets = [
        {record["text"].strip().casefold() for record in split}
        for split in (train, validation, test)
    ]
    if sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]:
        raise ValueError(
            "Duplicate utterances found across train, validation, and test splits"
        )


def evaluate(model, records: list[dict[str, str]], name: str) -> None:
    texts = [record["text"] for record in records]
    expected = [record["intent"] for record in records]
    predicted = model.predict(texts)
    labels = list(INTENTS)
    print(f"\n{name} ({len(records)} examples)")
    print(f"accuracy: {accuracy_score(expected, predicted):.3f}")
    print(
        classification_report(
            expected, predicted, labels=labels, zero_division=0, digits=3
        )
    )
    print("confusion matrix (rows=actual, columns=predicted):")
    print(confusion_matrix(expected, predicted, labels=labels))


def train() -> None:
    train_records = load_corpus()
    validation_records = _load_split(VALIDATION_PATH)
    test_records = _load_split(TEST_PATH)
    _assert_no_leakage(train_records, validation_records, test_records)

    model = build_model(train_records)
    evaluate(model, validation_records, "validation")
    evaluate(model, test_records, "test")
    save_model(model, MODEL_PATH)
    print(f"saved model: {MODEL_PATH}")


if __name__ == "__main__":
    train()
