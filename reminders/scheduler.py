"""Safe APScheduler lifecycle for the ANC reminder job."""

from __future__ import annotations

import logging
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler

from config import settings

from .anc_reminders import send_due_reminders

log = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None
_lock = Lock()


def create_scheduler(provider, timezone: str | None = None) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=timezone or settings.reminder_timezone)
    scheduler.add_job(
        lambda: send_due_reminders(provider),
        "cron",
        hour=settings.reminder_hour,
        minute=settings.reminder_minute,
        id="anc-reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler


def start_scheduler(provider) -> BackgroundScheduler | None:
    """Start one process-local scheduler when enabled."""
    global _scheduler
    if not settings.enable_reminder_scheduler:
        log.info("ANC reminder scheduler is disabled")
        return None
    with _lock:
        if _scheduler is None or not _scheduler.running:
            _scheduler = create_scheduler(provider)
            _scheduler.start()
            log.info("ANC reminder scheduler started")
        return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    with _lock:
        if _scheduler is not None and _scheduler.running:
            _scheduler.shutdown(wait=False)
            log.info("ANC reminder scheduler stopped")
        _scheduler = None
