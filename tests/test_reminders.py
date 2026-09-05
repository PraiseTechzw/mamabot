from datetime import date

from database.queries import InMemoryRepository
from messaging.test_provider import TestMessageProvider
from reminders.anc_reminders import send_due_reminders
from reminders.scheduler import create_scheduler, shutdown_scheduler


class FailingProvider:
    channel = "test"

    def send(self, recipient: str, text: str):
        raise RuntimeError("provider unavailable")


def test_due_reminder_is_localized_and_recorded_once():
    repository = InMemoryRepository()
    user = repository.get_or_create_user("0771234567", "sn")
    repository.user_channels[user.id] = "test"
    appointment = repository.add_appointment(user.phone_number, date(2026, 9, 5))
    provider = TestMessageProvider()

    assert send_due_reminders(provider, date(2026, 9, 5), repository) == 1
    assert len(provider.sent) == 1
    assert "Chiyeuchidzo" in provider.sent[0].text
    assert len(repository.reminders) == 1
    assert repository.reminders[0].status == "sent"
    assert repository.reminders[0].appointment_id == appointment.id

    assert send_due_reminders(provider, date(2026, 9, 5), repository) == 0
    assert len(provider.sent) == 1
    assert len(repository.reminders) == 1


def test_failed_delivery_is_recorded_and_can_be_retried():
    repository = InMemoryRepository()
    appointment = repository.add_appointment("0771234567", date(2026, 9, 5))

    assert send_due_reminders(FailingProvider(), date(2026, 9, 5), repository) == 0
    assert repository.reminders[0].status == "failed"
    assert repository.reminders[0].error_message == "provider unavailable"
    assert appointment.id in [
        item.id for item in repository.due_appointments(date(2026, 9, 5))
    ]

    provider = TestMessageProvider()
    assert send_due_reminders(provider, date(2026, 9, 5), repository) == 1
    assert repository.reminders[0].status == "sent"


def test_channel_provider_mapping_respects_saved_channel():
    repository = InMemoryRepository()
    user = repository.get_or_create_user("0771234567")
    repository.user_channels[user.id] = "sms"
    repository.add_appointment(user.phone_number, date(2026, 9, 5))
    sms = TestMessageProvider(channel="sms")
    whatsapp = TestMessageProvider(channel="whatsapp")

    assert (
        send_due_reminders(
            {"sms": sms, "whatsapp": whatsapp}, date(2026, 9, 5), repository
        )
        == 1
    )
    assert len(sms.sent) == 1
    assert not whatsapp.sent


def test_scheduler_has_one_configured_cron_job_and_shuts_down():
    scheduler = create_scheduler(TestMessageProvider(), timezone="UTC")
    try:
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "anc-reminders"
        assert jobs[0].max_instances == 1
    finally:
        shutdown_scheduler()
        if scheduler.running:
            scheduler.shutdown(wait=False)
