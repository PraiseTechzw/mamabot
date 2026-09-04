from datetime import date

from database.queries import repository


def create_appointment(phone_number: str, appointment_date: date): return repository.add_appointment(phone_number, appointment_date)
