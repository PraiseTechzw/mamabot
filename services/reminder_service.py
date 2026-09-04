from datetime import date

from database.queries import repository


def due_appointments(on_date: date): return repository.due_appointments(on_date)
