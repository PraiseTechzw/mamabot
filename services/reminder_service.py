from datetime import date

from database.models import Reminder
from database.queries import repository
from reminders.anc_reminders import send_due_reminders


def due_appointments(on_date: date):
    return repository.due_appointments(on_date)


def create_reminder(
    user_id: int,
    scheduled_for,
    appointment_id: int | None = None,
    reminder_type: str = "appointment",
):
    return repository.create_reminder(
        Reminder(None, user_id, scheduled_for, appointment_id, reminder_type)
    )


def send_due(provider, on_date: date | None = None, repository_override=None) -> int:
    return send_due_reminders(provider, on_date, repository_override or repository)
