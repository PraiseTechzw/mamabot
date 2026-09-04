"""Registration validation helpers."""
from utils.validators import validate_phone_number


def validate_registration(phone_number: str, language: str) -> tuple[bool, str]:
    if not validate_phone_number(phone_number): return False, "A valid Zimbabwe mobile number is required."
    if language not in {"en", "sn", "nd"}: return False, "Language must be en, sn, or nd."
    return True, "ok"
