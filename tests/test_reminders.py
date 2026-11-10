import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app.services import reminders

HARARE = ZoneInfo("Africa/Harare")


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2026, 11, 10, 9, 0, tzinfo=HARARE)
        return value if tz else value.replace(tzinfo=None)


class ReminderSchedulingTests(unittest.TestCase):
    @patch("app.services.reminders.db.create_reminders", side_effect=lambda rows: rows)
    @patch(
        "app.services.reminders.db.get_patient",
        return_value={
            "phone_number": "+263771234567",
            "reminders_enabled": True,
            "consent_at": "2026-11-01T10:00:00+02:00",
            "due_date": "2026-12-01",
        },
    )
    def test_weekly_messages_are_scheduled_wednesdays_in_harare(self, get_patient, create):
        with patch("app.services.reminders.datetime", FrozenDateTime):
            scheduled = reminders.schedule_weekly_pregnancy_reminders(
                "+263771234567",
                ["Week one", "Week two", "Week three"],
            )

        self.assertEqual(len(scheduled), 3)
        self.assertEqual(
            [datetime.fromisoformat(item["scheduled_at"]).astimezone(HARARE).isoformat()
             for item in scheduled],
            [
                "2026-11-11T10:00:00+02:00",
                "2026-11-18T10:00:00+02:00",
                "2026-11-25T10:00:00+02:00",
            ],
        )
        create.assert_called_once()
        get_patient.assert_called_once_with("+263771234567")

    @patch("app.services.reminders.db.create_reminders", side_effect=lambda rows: rows)
    @patch("app.services.reminders.db.create_appointment", return_value={"id": "test-id"})
    @patch(
        "app.services.reminders.db.get_patient",
        return_value={
            "phone_number": "+263771234567",
            "reminders_enabled": True,
            "consent_at": "2026-11-01T10:00:00+02:00",
        },
    )
    def test_appointment_schedules_seven_day_and_one_day_reminders(
        self, get_patient, create_appointment, create_reminders
    ):
        with patch("app.services.reminders.datetime", FrozenDateTime):
            appointment = reminders.schedule_appointment_reminders(
                "+263771234567",
                "2026-11-20T13:00:00+02:00",
                "ANC appointment reminder",
            )

        self.assertEqual(appointment["id"], "test-id")
        self.assertEqual(len(appointment["reminders"]), 2)
        self.assertEqual(create_appointment.call_count, 1)
        self.assertEqual(create_reminders.call_count, 1)
        get_patient.assert_called_once_with("+263771234567")

    @patch(
        "app.services.reminders.db.get_patient",
        return_value={
            "phone_number": "+263771234567",
            "reminders_enabled": False,
            "consent_at": None,
        },
    )
    def test_reminder_requires_recorded_consent(self, get_patient):
        with self.assertRaises(PermissionError):
            reminders.schedule_reminder(
                "+263771234567",
                "A reminder",
                "2026-11-20T13:00:00+02:00",
            )
        get_patient.assert_called_once_with("+263771234567")


if __name__ == "__main__":
    unittest.main()
