"""ANC reminder job; delivery is injected through a provider."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from database.queries import repository as default_repository


def send_due_reminders(provider, on_date: date | None = None, repository=default_repository) -> int:
    sent = 0
    for appointment in repository.due_appointments(on_date or datetime.now(ZoneInfo("Africa/Harare")).date()):
        user = next((u for u in repository.users.values() if u.id == appointment.user_id), None)
        if not user:
            continue
        provider.send(
            user.phone_number,
            "MamaBot reminder: please attend your antenatal care appointment today. Contact your clinic if you need help.",
        )
        repository.mark_reminder_sent(appointment.id or 0)
        sent += 1
    return sent
