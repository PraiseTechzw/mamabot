"""Conservative escalation helpers; no diagnosis is performed."""

from database.models import Escalation

DANGER_INTENTS = {"danger_sign_query", "nurse_escalation", "escalation_to_nurse"}


def requires_escalation(intent: str) -> bool:
    return intent in DANGER_INTENTS


def persist_escalation(
    repository: object,
    user_id: int,
    reason: str,
    conversation_id: int | None = None,
    severity: str = "urgent",
) -> Escalation | None:
    """Persist an escalation when the active repository supports it."""
    create = getattr(repository, "create_escalation", None)
    if create is None:
        return None
    return create(
        Escalation(
            id=None,
            user_id=user_id,
            reason=reason,
            severity=severity,
            conversation_id=conversation_id,
        )
    )
