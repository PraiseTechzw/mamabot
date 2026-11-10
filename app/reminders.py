"""One-shot and looped worker for scheduled WhatsApp reminders."""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timezone

from app import create_app, db
from app.services.messaging import send_whatsapp_reminder

logger = logging.getLogger(__name__)


def dispatch_due_reminders(limit: int = 50) -> dict[str, int]:
    jobs = db.claim_due_reminders(limit)
    sent = 0
    failed = 0

    for job in jobs:
        try:
            patient = db.get_patient(job["phone_number"])
            if not patient or not patient.get("reminders_enabled") or not patient.get("consent_at"):
                db.update_reminder(job["id"], {"status": "cancelled"})
                continue
            result = send_whatsapp_reminder(job["phone_number"], job["content"])
        except Exception as exc:
            failed += 1
            try:
                db.update_reminder(
                    job["id"],
                    {"status": "failed", "last_error": str(exc)[:500]},
                )
            except Exception:
                logger.exception("Could not save failed reminder status")
            logger.exception("Could not send reminder %s", job.get("id"))
            continue

        try:
            db.update_reminder(
                job["id"],
                {
                    "status": "sent",
                    "provider_message_id": result.message_id,
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "last_error": None,
                },
            )
            sent += 1
        except Exception:
            logger.exception(
                "Twilio accepted reminder %s but Supabase status could not be updated",
                job.get("id"),
            )
            failed += 1

    return {"claimed": len(jobs), "sent": sent, "failed": failed}


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch due MamaBot reminders")
    parser.add_argument("--loop", action="store_true", help="Run continuously as a worker")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between worker runs")
    args = parser.parse_args()
    if args.interval < 10:
        parser.error("--interval must be at least 10 seconds")

    app = create_app("production")
    logging.basicConfig(level=logging.INFO)

    with app.app_context():
        while True:
            try:
                result = dispatch_due_reminders()
                logger.info("Reminder dispatch: %s", result)
            except Exception:
                logger.exception("Reminder dispatch run failed")
                if not args.loop:
                    return 1
            if not args.loop:
                return 1 if result["failed"] else 0
            time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
