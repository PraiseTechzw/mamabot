"""Input validation and normalization."""
import re


def validate_phone_number(value: str) -> bool: return bool(re.fullmatch(r"(?:\+263|0)7\d{8}", value.strip()))
def validate_message(value: object, maximum: int = 1000) -> str:
    if not isinstance(value, str): raise TypeError("message must be a string")
    value = value.strip()
    if not value: raise ValueError("message cannot be empty")
    if len(value) > maximum: raise ValueError(f"message exceeds {maximum} characters")
    return value
