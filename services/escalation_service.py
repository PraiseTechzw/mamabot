from config import settings
from database.models import Escalation
from database.queries import repository


def escalation_destination() -> str:
    return settings.nurse_phone_number


def create_escalation(
    user_id: int,
    reason: str,
    severity: str = "urgent",
    conversation_id: int | None = None,
):
    return repository.create_escalation(
        Escalation(None, user_id, reason, severity, conversation_id=conversation_id)
    )


def resolve_escalation(escalation_id: int) -> None:
    repository.close_escalation(escalation_id)
