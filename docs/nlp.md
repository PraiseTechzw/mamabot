# NLP

The local pipeline applies Unicode normalization, profile-backed language detection, a trained TF-IDF word/character logistic-regression intent model, and workflow entity extraction. Intent classification is separate from language detection and entity extraction.

The six intents are `appointment_reminder`, `danger_sign_query`, `nutrition_information`, `language_switch`, `general_greeting`, and `nurse_escalation`. Danger signs are a safety/escalation category, never a diagnosis. Low-confidence predictions use the configured threshold `INTENT_CONFIDENCE_THRESHOLD`; danger-sign results retain urgent non-diagnostic guidance.

Train the model with:

```bash
.venv/bin/python scripts/train_nlp.py
```

This checks train/validation/test leakage, prints accuracy, precision, recall, F1, and confusion matrices, and writes `models/intent/model.pkl`. The artifact is ignored by Git and must be generated during deployment/build. Runtime requests do not train or write models.

Entity extraction covers only workflow data: names, phone numbers, languages, general dates, due dates, and appointment dates. Dates are normalized to ISO format and validated before registration persistence.
