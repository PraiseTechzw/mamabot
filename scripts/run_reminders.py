"""Manually trigger due ANC reminders for development and operations."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import settings
from database.queries import repository
from messaging.test_provider import TestMessageProvider
from reminders.anc_reminders import send_due_reminders


def main() -> None:
    parser = argparse.ArgumentParser(description="Send due MamaBot ANC reminders")
    parser.add_argument(
        "--date", dest="reminder_date", help="YYYY-MM-DD; defaults to today"
    )
    args = parser.parse_args()
    target = (
        date.fromisoformat(args.reminder_date)
        if args.reminder_date
        else datetime.now().astimezone().date()
    )
    provider = TestMessageProvider()
    count = send_due_reminders(provider, target, repository, settings.reminder_timezone)
    print(f"sent={count}")
    for message in provider.sent:
        print(f"{message.channel}: {message.recipient}: {message.text}")


if __name__ == "__main__":
    main()
