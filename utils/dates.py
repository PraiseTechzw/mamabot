"""Date parsing used by appointment reminders."""
from datetime import date


def parse_iso_date(value: str) -> date:
    try: return date.fromisoformat(value)
    except ValueError as exc: raise ValueError("date must use YYYY-MM-DD") from exc
