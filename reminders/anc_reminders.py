"""ANC reminder job; delivery is injected through the messaging abstraction."""

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from database.models import Reminder
from database.queries import repository as default_repository
from reminders.templates import appointment_reminder

log = logging.getLogger(__name__)


def send_due_reminders(
    provider,
    on_date: date | None = None,
    repository=default_repository,
    timezone_name: str = "Africa/Harare",
) -> int:
    timezone_info = ZoneInfo(timezone_name)
    sent = 0
    for appointment in repository.due_appointments(
        on_date or datetime.now(timezone_info).date()
    ):
        user = repository.get_user_by_id(appointment.user_id)
        if not user:
            continue
        appointment_id = appointment.id or 0
        if repository.reminder_was_sent(appointment_id):
            continue
        reminder = repository.create_reminder(
            Reminder(
                None,
                user.id or 0,
                datetime.now(timezone_info),
                appointment_id,
            )
        )
        channel = repository.get_user_channel(user.id or 0)
        selected_provider = (
            provider.get(channel) if isinstance(provider, dict) else provider
        )
        if selected_provider is None:
            repository.update_reminder_status(
                reminder.id or 0, "failed", f"No provider for channel: {channel}"
            )
            log.error(
                "No reminder provider for channel=%s appointment=%s",
                channel,
                appointment_id,
            )
            continue
        text = appointment_reminder(user.language, appointment.appointment_date)
        try:
            selected_provider.send(user.phone_number, text)
        except Exception as exc:
            repository.update_reminder_status(
                reminder.id or 0, "failed", str(exc)[:500]
            )
            log.exception("Reminder delivery failed for appointment=%s", appointment_id)
            continue
        repository.update_reminder_status(reminder.id or 0, "sent")
        repository.mark_reminder_sent(appointment_id)
        sent += 1
        log.info(
            "Reminder sent appointment=%s user=%s channel=%s",
            appointment_id,
            user.id,
            channel,
        )
    return sent
