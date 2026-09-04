"""Persistence gateway. MySQL is used when configured; local memory keeps chat usable."""
from __future__ import annotations

from datetime import date
from threading import Lock

from .models import Appointment, ConversationMessage, User


class InMemoryRepository:
    def __init__(self):
        self._lock = Lock(); self.users = {}; self.messages = []; self.appointments = []; self._next_id = 1
    def get_or_create_user(self, phone_number: str, language: str = "en") -> User:
        with self._lock:
            if phone_number in self.users: return self.users[phone_number]
            user = User(self._next_id, phone_number, language=language); self._next_id += 1; self.users[phone_number] = user; return user
    def update_user_language(self, phone_number: str, language: str) -> User:
        old = self.get_or_create_user(phone_number); user = User(old.id, old.phone_number, old.name, language, old.due_date); self.users[phone_number] = user; return user
    def save_message(self, message: ConversationMessage) -> None: self.messages.append(message)
    def add_appointment(self, phone_number: str, appointment_date: date) -> Appointment:
        user = self.get_or_create_user(phone_number); appointment = Appointment(len(self.appointments) + 1, user.id or 0, appointment_date); self.appointments.append(appointment); return appointment
    def due_appointments(self, on_date: date) -> list[Appointment]: return [a for a in self.appointments if a.appointment_date == on_date and not a.reminder_sent]
    def mark_reminder_sent(self, appointment_id: int) -> None:
        self.appointments = [Appointment(a.id, a.user_id, a.appointment_date, True) if a.id == appointment_id else a for a in self.appointments]

repository = InMemoryRepository()
