"""Small, conservative entity extractor for registration and reminders."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Entities:
    phone_number: str | None = None
    due_date: str | None = None
    appointment_date: str | None = None
    language: str | None = None

def extract_entities(text: str) -> Entities:
    phone = next(iter(re.findall(r"(?:\+263|0)7\d{8}", text)), None)
    date = next(iter(re.findall(r"\b(?:20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b", text)), None)
    lowered = text.lower()
    language = "sn" if "shona" in lowered or "chishona" in lowered else "nd" if "ndebele" in lowered or "isi ndebele" in lowered else "en" if "english" in lowered else None
    return Entities(phone_number=phone, due_date=date, appointment_date=date, language=language)
