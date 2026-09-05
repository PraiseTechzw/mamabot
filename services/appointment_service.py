from datetime import date

from database.queries import repository


def create_appointment(
    phone_number: str,
    appointment_date: date,
    appointment_type: str = "anc",
    pregnancy_profile_id: int | None = None,
):
    return repository.add_appointment(
        phone_number, appointment_date, appointment_type, pregnancy_profile_id
    )


def due_appointments(on_date: date):
    return repository.due_appointments(on_date)


def mark_reminder_sent(appointment_id: int) -> None:
    repository.mark_reminder_sent(appointment_id)
