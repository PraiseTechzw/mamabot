"""Parameterized persistence gateways for MySQL and local development."""

from __future__ import annotations

from datetime import UTC, date, datetime
from threading import Lock
from typing import Any

from config import settings

from .connection import get_cursor
from .models import (
    Appointment,
    Conversation,
    ConversationMessage,
    Escalation,
    HealthWorker,
    PregnancyProfile,
    Reminder,
    User,
)


def _user(row: dict[str, Any]) -> User:
    return User(
        row["id"],
        row["phone_number"],
        row.get("name"),
        row.get("language", row.get("preferred_language", "en")),
        row.get("due_date"),
        row.get("created_at"),
        row.get("updated_at"),
    )


def _appointment(row: dict[str, Any]) -> Appointment:
    return Appointment(
        row["id"],
        row["user_id"],
        row["appointment_date"],
        bool(row["reminder_sent"]),
        row.get("appointment_type", "anc"),
        row.get("status", "scheduled"),
        row.get("pregnancy_profile_id"),
        row.get("created_at"),
        row.get("updated_at"),
    )


class MySQLRepository:
    """Persistence gateway. Every value is passed separately to the connector."""

    def get_or_create_user(self, phone_number: str, language: str = "en") -> User:
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT IGNORE INTO users (phone_number, preferred_language) VALUES (%s, %s)",
                (phone_number, language),
            )
            cursor.execute(
                "SELECT * FROM users WHERE phone_number = %s", (phone_number,)
            )
            row = cursor.fetchone()
        if not row:
            raise RuntimeError("User could not be created")
        return _user(row)

    def get_user_by_phone(self, phone_number: str) -> User | None:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE phone_number = %s", (phone_number,)
            )
            row = cursor.fetchone()
        return _user(row) if row else None

    def update_user_language(self, phone_number: str, language: str) -> User:
        with get_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET preferred_language = %s WHERE phone_number = %s",
                (language, phone_number),
            )
        return self.get_or_create_user(phone_number, language)

    def get_user_by_id(self, user_id: int) -> User | None:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
        return _user(row) if row else None

    def update_user(
        self, user_id: int, name: str | None = None, due_date: date | None = None
    ) -> User | None:
        with get_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET name = %s, due_date = %s WHERE id = %s",
                (name, due_date, user_id),
            )
        return self.get_user_by_id(user_id)

    def register_user(
        self,
        phone_number: str,
        name: str,
        language: str,
        due_date: date,
        channel: str,
    ) -> tuple[User, PregnancyProfile]:
        """Create or update a user record and their pregnancy profile atomically.

        If a user with *phone_number* already exists their name, language and
        due_date are updated in-place.  The pregnancy profile is inserted as a
        new row so a history is preserved.

        Returns (User, PregnancyProfile).
        """
        with get_cursor() as cursor:
            # Upsert the user row
            cursor.execute(
                """INSERT INTO users (phone_number, name, preferred_language, due_date)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                       name             = VALUES(name),
                       preferred_language = VALUES(preferred_language),
                       due_date         = VALUES(due_date)
                """,
                (phone_number, name, language, due_date),
            )
            cursor.execute(
                "SELECT * FROM users WHERE phone_number = %s", (phone_number,)
            )
            user_row = cursor.fetchone()
            if not user_row:
                raise RuntimeError("User could not be registered")
            user = _user(user_row)

            # Insert a new pregnancy profile
            cursor.execute(
                """INSERT INTO pregnancy_profiles (user_id, due_date)
                   VALUES (%s, %s)
                """,
                (user.id, due_date),
            )
            profile_id = cursor.lastrowid
            cursor.execute(
                "SELECT * FROM pregnancy_profiles WHERE id = %s", (profile_id,)
            )
            profile_row = cursor.fetchone()

            # Record the user's preferred channel
            cursor.execute(
                """INSERT INTO user_channels (user_id, channel_code, address, is_primary)
                   VALUES (%s, %s, %s, TRUE)
                   ON DUPLICATE KEY UPDATE is_primary = TRUE
                """,
                (user.id, channel, phone_number),
            )

        profile = PregnancyProfile(
            profile_row["id"],
            profile_row["user_id"],
            profile_row.get("last_menstrual_period"),
            profile_row.get("due_date"),
            profile_row.get("gravida"),
            profile_row.get("parity"),
            profile_row.get("notes"),
            profile_row.get("created_at"),
            profile_row.get("updated_at"),
        )
        return user, profile

    def save_pregnancy_profile(self, profile: PregnancyProfile) -> PregnancyProfile:
        with get_cursor() as cursor:
            if profile.id is None:
                cursor.execute(
                    "INSERT INTO pregnancy_profiles (user_id, last_menstrual_period, due_date, gravida, parity, notes) VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        profile.user_id,
                        profile.last_menstrual_period,
                        profile.due_date,
                        profile.gravida,
                        profile.parity,
                        profile.notes,
                    ),
                )
                profile_id = cursor.lastrowid
            else:
                cursor.execute(
                    "UPDATE pregnancy_profiles SET last_menstrual_period = %s, due_date = %s, gravida = %s, parity = %s, notes = %s WHERE id = %s",
                    (
                        profile.last_menstrual_period,
                        profile.due_date,
                        profile.gravida,
                        profile.parity,
                        profile.notes,
                        profile.id,
                    ),
                )
                profile_id = profile.id
            cursor.execute(
                "SELECT * FROM pregnancy_profiles WHERE id = %s", (profile_id,)
            )
            row = cursor.fetchone()
        return PregnancyProfile(**row)

    def get_pregnancy_profile(self, user_id: int) -> PregnancyProfile | None:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM pregnancy_profiles WHERE user_id = %s ORDER BY id DESC LIMIT 1",
                (user_id,),
            )
            row = cursor.fetchone()
        return PregnancyProfile(**row) if row else None

    def get_or_create_conversation(
        self, user_id: int | None, channel: str
    ) -> Conversation:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM conversations WHERE user_id <=> %s AND channel_code = %s AND status = 'open' ORDER BY id DESC LIMIT 1",
                (user_id, channel),
            )
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    "INSERT INTO conversations (user_id, channel_code) VALUES (%s, %s)",
                    (user_id, channel),
                )
                conversation_id = cursor.lastrowid
                cursor.execute(
                    "SELECT * FROM conversations WHERE id = %s", (conversation_id,)
                )
                row = cursor.fetchone()
        return Conversation(
            row["id"],
            row["user_id"],
            row["channel_code"],
            row["status"],
            row.get("started_at"),
            row.get("last_message_at"),
        )

    def save_message(self, message: ConversationMessage) -> ConversationMessage:
        conversation = (
            self.get_or_create_conversation(message.user_id, message.channel)
            if message.conversation_id is None
            else None
        )
        conversation_id = message.conversation_id or conversation.id
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO messages (conversation_id, user_id, direction, language_code, message_text, created_at) VALUES (%s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))",
                (
                    conversation_id,
                    message.user_id,
                    message.direction,
                    message.language,
                    message.text,
                    message.created_at,
                ),
            )
            message_id = cursor.lastrowid
            cursor.execute(
                "UPDATE conversations SET last_message_at = COALESCE(%s, CURRENT_TIMESTAMP) WHERE id = %s",
                (message.created_at, conversation_id),
            )
        return ConversationMessage(
            message_id,
            message.user_id,
            message.channel,
            message.direction,
            message.text,
            message.created_at,
            conversation_id,
            message.language,
        )

    def list_messages(
        self, conversation_id: int, limit: int = 100
    ) -> list[ConversationMessage]:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT m.*, c.channel_code FROM messages m JOIN conversations c ON c.id = m.conversation_id WHERE m.conversation_id = %s ORDER BY m.created_at, m.id LIMIT %s",
                (conversation_id, limit),
            )
            rows = cursor.fetchall()
        return [
            ConversationMessage(
                row["id"],
                row["user_id"],
                row["channel_code"],
                row["direction"],
                row["message_text"],
                row.get("created_at"),
                row["conversation_id"],
                row["language_code"],
            )
            for row in rows
        ]

    def add_appointment(
        self,
        phone_number: str,
        appointment_date: date,
        appointment_type: str = "anc",
        pregnancy_profile_id: int | None = None,
    ) -> Appointment:
        user = self.get_or_create_user(phone_number)
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO appointments (user_id, pregnancy_profile_id, appointment_type, appointment_date) VALUES (%s, %s, %s, %s)",
                (user.id, pregnancy_profile_id, appointment_type, appointment_date),
            )
            appointment_id = cursor.lastrowid
            cursor.execute(
                "SELECT * FROM appointments WHERE id = %s", (appointment_id,)
            )
            row = cursor.fetchone()
        return _appointment(row)

    def due_appointments(self, on_date: date) -> list[Appointment]:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM appointments WHERE appointment_date = %s AND reminder_sent = FALSE AND status = 'scheduled' ORDER BY appointment_date, id",
                (on_date,),
            )
            rows = cursor.fetchall()
        return [_appointment(row) for row in rows]

    def mark_reminder_sent(self, appointment_id: int) -> None:
        with get_cursor() as cursor:
            cursor.execute(
                "UPDATE appointments SET reminder_sent = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (appointment_id,),
            )

    def create_reminder(self, reminder: Reminder) -> Reminder:
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO reminders (user_id, appointment_id, reminder_type, scheduled_for) VALUES (%s, %s, %s, %s)",
                (
                    reminder.user_id,
                    reminder.appointment_id,
                    reminder.reminder_type,
                    reminder.scheduled_for,
                ),
            )
            reminder_id = cursor.lastrowid
            cursor.execute("SELECT * FROM reminders WHERE id = %s", (reminder_id,))
            row = cursor.fetchone()
        return Reminder(
            row["id"],
            row["user_id"],
            row["scheduled_for"],
            row.get("appointment_id"),
            row["reminder_type"],
            row["status"],
            row.get("sent_at"),
        )

    def create_health_worker(self, worker: HealthWorker) -> HealthWorker:
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO health_workers (name, phone_number, email, active) VALUES (%s, %s, %s, %s)",
                (worker.name, worker.phone_number, worker.email, worker.active),
            )
            worker_id = cursor.lastrowid
            cursor.execute("SELECT * FROM health_workers WHERE id = %s", (worker_id,))
            row = cursor.fetchone()
        return HealthWorker(
            row["id"],
            row["name"],
            row.get("phone_number"),
            row.get("email"),
            bool(row["active"]),
        )

    def create_escalation(self, escalation: Escalation) -> Escalation:
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO escalations (user_id, conversation_id, assigned_health_worker_id, reason, severity) VALUES (%s, %s, %s, %s, %s)",
                (
                    escalation.user_id,
                    escalation.conversation_id,
                    escalation.assigned_health_worker_id,
                    escalation.reason,
                    escalation.severity,
                ),
            )
            escalation_id = cursor.lastrowid
            cursor.execute("SELECT * FROM escalations WHERE id = %s", (escalation_id,))
            row = cursor.fetchone()
        return Escalation(
            row["id"],
            row["user_id"],
            row["reason"],
            row["severity"],
            row["status"],
            row.get("conversation_id"),
            row.get("assigned_health_worker_id"),
            row.get("created_at"),
            row.get("resolved_at"),
        )

    def close_escalation(self, escalation_id: int) -> None:
        with get_cursor() as cursor:
            cursor.execute(
                "UPDATE escalations SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP WHERE id = %s",
                (escalation_id,),
            )


class InMemoryRepository:
    def __init__(self):
        self._lock = Lock()
        self.users: dict[str, User] = {}
        self.messages: list[ConversationMessage] = []
        self.conversations: list[Conversation] = []
        self.appointments: list[Appointment] = []
        self.profiles: list[PregnancyProfile] = []
        self.reminders: list[Reminder] = []
        self.escalations: list[Escalation] = []
        self._next_id = 1

    # ------------------------------------------------------------------
    # User helpers
    # ------------------------------------------------------------------

    def get_or_create_user(self, phone_number: str, language: str = "en") -> User:
        with self._lock:
            if phone_number in self.users:
                return self.users[phone_number]
            user = User(self._next_id, phone_number, language=language)
            self._next_id += 1
            self.users[phone_number] = user
            return user

    def get_user_by_phone(self, phone_number: str) -> User | None:
        return self.users.get(phone_number)

    def get_user_by_id(self, user_id: int) -> User | None:
        return next((user for user in self.users.values() if user.id == user_id), None)

    def update_user_language(self, phone_number: str, language: str) -> User:
        old = self.get_or_create_user(phone_number)
        user = User(old.id, old.phone_number, old.name, language, old.due_date)
        self.users[phone_number] = user
        return user

    def update_user(
        self, user_id: int, name: str | None = None, due_date: date | None = None
    ) -> User | None:
        old = self.get_user_by_id(user_id)
        if not old:
            return None
        user = User(old.id, old.phone_number, name, old.language, due_date)
        self.users[user.phone_number] = user
        return user

    def register_user(
        self,
        phone_number: str,
        name: str,
        language: str,
        due_date: date,
        channel: str,
    ) -> tuple[User, PregnancyProfile]:
        """Create or update user + pregnancy profile atomically."""
        with self._lock:
            existing = self.users.get(phone_number)
            user_id = existing.id if existing else self._next_id
            if not existing:
                self._next_id += 1
            user = User(user_id, phone_number, name, language, due_date)
            self.users[phone_number] = user

        profile = PregnancyProfile(
            id=len(self.profiles) + 1,
            user_id=user_id,
            due_date=due_date,
        )
        with self._lock:
            self.profiles.append(profile)
        return user, profile

    # ------------------------------------------------------------------
    # Pregnancy profile helpers
    # ------------------------------------------------------------------

    def save_pregnancy_profile(self, profile: PregnancyProfile) -> PregnancyProfile:
        saved = PregnancyProfile(
            profile.id or len(self.profiles) + 1,
            profile.user_id,
            profile.last_menstrual_period,
            profile.due_date,
            profile.gravida,
            profile.parity,
            profile.notes,
        )
        self.profiles = [item for item in self.profiles if item.id != saved.id] + [
            saved
        ]
        return saved

    def get_pregnancy_profile(self, user_id: int) -> PregnancyProfile | None:
        return next(
            (
                profile
                for profile in reversed(self.profiles)
                if profile.user_id == user_id
            ),
            None,
        )

    # ------------------------------------------------------------------
    # Conversation / message helpers
    # ------------------------------------------------------------------

    def get_or_create_conversation(
        self, user_id: int | None, channel: str
    ) -> Conversation:
        conversation = next(
            (
                item
                for item in reversed(self.conversations)
                if item.user_id == user_id
                and item.channel == channel
                and item.status == "open"
            ),
            None,
        )
        if conversation:
            return conversation
        conversation = Conversation(len(self.conversations) + 1, user_id, channel)
        self.conversations.append(conversation)
        return conversation

    def save_message(self, message: ConversationMessage) -> ConversationMessage:
        if message.conversation_id is None:
            conversation = self.get_or_create_conversation(
                message.user_id, message.channel
            )
        else:
            conversation = next(
                item
                for item in self.conversations
                if item.id == message.conversation_id
            )
        saved = ConversationMessage(
            len(self.messages) + 1,
            message.user_id,
            message.channel,
            message.direction,
            message.text,
            message.created_at,
            conversation.id,
            message.language,
        )
        self.messages.append(saved)
        return saved

    def list_messages(
        self, conversation_id: int, limit: int = 100
    ) -> list[ConversationMessage]:
        return [
            message
            for message in self.messages
            if message.conversation_id == conversation_id
        ][:limit]

    # ------------------------------------------------------------------
    # Appointment helpers
    # ------------------------------------------------------------------

    def add_appointment(
        self,
        phone_number: str,
        appointment_date: date,
        appointment_type: str = "anc",
        pregnancy_profile_id: int | None = None,
    ) -> Appointment:
        user = self.get_or_create_user(phone_number)
        appointment = Appointment(
            len(self.appointments) + 1,
            user.id or 0,
            appointment_date,
            appointment_type=appointment_type,
            pregnancy_profile_id=pregnancy_profile_id,
        )
        self.appointments.append(appointment)
        return appointment

    def due_appointments(self, on_date: date) -> list[Appointment]:
        return [
            a
            for a in self.appointments
            if a.appointment_date == on_date and not a.reminder_sent
        ]

    def mark_reminder_sent(self, appointment_id: int) -> None:
        self.appointments = [
            (
                Appointment(a.id, a.user_id, a.appointment_date, True)
                if a.id == appointment_id
                else a
            )
            for a in self.appointments
        ]

    # ------------------------------------------------------------------
    # Reminder helpers
    # ------------------------------------------------------------------

    def create_reminder(self, reminder: Reminder) -> Reminder:
        saved = Reminder(
            reminder.id or len(self.reminders) + 1,
            reminder.user_id,
            reminder.scheduled_for,
            reminder.appointment_id,
            reminder.reminder_type,
            reminder.status,
            reminder.sent_at,
        )
        self.reminders.append(saved)
        return saved

    # ------------------------------------------------------------------
    # Escalation helpers
    # ------------------------------------------------------------------

    def create_escalation(self, escalation: Escalation) -> Escalation:
        saved = Escalation(
            escalation.id or len(self.escalations) + 1,
            escalation.user_id,
            escalation.reason,
            escalation.severity,
            escalation.status,
            escalation.conversation_id,
            escalation.assigned_health_worker_id,
            escalation.created_at,
            escalation.resolved_at,
        )
        self.escalations.append(saved)
        return saved

    def close_escalation(self, escalation_id: int) -> None:
        self.escalations = [
            (
                Escalation(
                    item.id,
                    item.user_id,
                    item.reason,
                    item.severity,
                    "resolved",
                    item.conversation_id,
                    item.assigned_health_worker_id,
                    item.created_at,
                    datetime.now(UTC),
                )
                if item.id == escalation_id
                else item
            )
            for item in self.escalations
        ]


def create_repository() -> MySQLRepository | InMemoryRepository:
    if settings.database_backend == "mysql":
        return MySQLRepository()
    return InMemoryRepository()


repository = create_repository()
