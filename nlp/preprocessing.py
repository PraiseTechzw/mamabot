"""Text normalization helpers."""
import re


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("message must be text")
    return re.sub(r"\s+", " ", text.strip())
