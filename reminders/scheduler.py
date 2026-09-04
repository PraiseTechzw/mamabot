"""Optional APScheduler integration, disabled by default in local development."""
from apscheduler.schedulers.background import BackgroundScheduler

from .anc_reminders import send_due_reminders


def create_scheduler(provider, timezone: str = "Africa/Harare"):
    scheduler = BackgroundScheduler(timezone=timezone)
    scheduler.add_job(lambda: send_due_reminders(provider), "cron", hour=8, minute=0, id="anc-reminders", replace_existing=True)
    return scheduler
