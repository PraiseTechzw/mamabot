"""Run a non-destructive local smoke test of MamaBot's NLP engine."""

import sys

from app.nlp.engine import get_engine

TEST_CASES = [
    ("hello", "greeting"),
    ("mhoro", "greeting"),
    ("sawubona", "greeting"),
    ("I have heavy bleeding", "danger_signs"),
    ("what should I eat", "nutrition"),
    ("find nearest clinic", "clinic_visits"),
    ("ndinoda kuona chipatara", "clinic_visits"),
    ("how many antenatal visits", "clinic_visits"),
    ("ndiri nani pane mimba", "pregnancy_stages"),
    ("signs of labour", "labour_delivery"),
    ("breastfeeding after birth", "newborn_care"),
    ("HIV during pregnancy PMTCT", "hiv_pmtct"),
]


def main() -> int:
    engine = get_engine()
    passed = 0

    print("\nMamaBot NLP smoke test")
    for text, expected in TEST_CASES:
        predicted, confidence = engine.predict_intent(text)
        success = predicted == expected
        passed += int(success)
        marker = "PASS" if success else "FAIL"
        print(f"{marker}: {text!r} -> {predicted} ({confidence:.2f}); expected {expected}")

    for language in ("english", "shona", "ndebele"):
        response = engine.get_response("danger_signs", language)
        if not response:
            print(f"FAIL: missing danger-sign response for {language}")
            return 1

    print(f"\n{passed}/{len(TEST_CASES)} intent checks passed")
    return 0 if passed == len(TEST_CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
