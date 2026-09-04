"""Conservative escalation helpers; no diagnosis is performed."""
DANGER_INTENTS = {"danger_sign_query", "escalation_to_nurse"}

def requires_escalation(intent: str) -> bool: return intent in DANGER_INTENTS
