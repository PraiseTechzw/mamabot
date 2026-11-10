"""Reproducible held-out evaluation of the configured intent examples."""

import json
from datetime import datetime, timezone

from sklearn.base import clone
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

from app.nlp.engine import get_engine

RANDOM_STATE = 42
TEST_SIZE = 0.2
REPORT_PATH = "evaluation_report.json"


def main() -> int:
    engine = get_engine()
    engine.retrain()

    texts = []
    labels = []
    for intent in engine.intents_data["intents"]:
        for pattern in intent["patterns"]:
            texts.append(engine._preprocess(pattern))
            labels.append(intent["tag"])

    if not texts:
        raise ValueError("No intent patterns found in data/intents/intents.json")

    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts,
        labels,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=labels,
    )
    train_encoded = engine.label_encoder.transform(train_labels)

    classifier = clone(engine.pipeline)
    classifier.fit(train_texts, train_encoded)
    predicted_encoded = classifier.predict(test_texts)
    predicted_labels = engine.label_encoder.inverse_transform(predicted_encoded)
    class_names = list(engine.label_encoder.classes_)

    report = classification_report(
        test_labels,
        predicted_labels,
        labels=class_names,
        output_dict=True,
        zero_division=0,
    )
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation": {
            "method": "stratified random holdout of intent patterns",
            "source": "data/intents/intents.json",
            "random_state": RANDOM_STATE,
            "test_fraction": TEST_SIZE,
            "pattern_count": len(texts),
            "training_pattern_count": len(train_texts),
            "test_pattern_count": len(test_texts),
            "intent_count": len(class_names),
            "limitations": [
                "Pattern-level classification only; patterns are curated examples, not an independent user corpus.",
                "Language identification, clinical correctness, usability, and message delivery are not evaluated.",
            ],
        },
        "metrics": {
            "accuracy": accuracy_score(test_labels, predicted_labels),
            "macro_f1": f1_score(
                test_labels,
                predicted_labels,
                labels=class_names,
                average="macro",
                zero_division=0,
            ),
            "per_intent": {
                name: report[name]
                for name in class_names
            },
            "confusion_matrix": {
                "labels": class_names,
                "values": confusion_matrix(
                    test_labels,
                    predicted_labels,
                    labels=class_names,
                ).tolist(),
            },
        },
        "failed_cases": [
            {"pattern": text, "expected": expected, "predicted": predicted}
            for text, expected, predicted in zip(
                test_texts,
                test_labels,
                predicted_labels,
            )
            if expected != predicted
        ],
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
        json.dump(result, report_file, indent=2, ensure_ascii=False)
        report_file.write("\n")

    print(
        f"Evaluated {len(test_texts)} held-out patterns across "
        f"{len(class_names)} intents; accuracy={result['metrics']['accuracy']:.3f}, "
        f"macro_f1={result['metrics']['macro_f1']:.3f}."
    )
    print(f"Report written to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
