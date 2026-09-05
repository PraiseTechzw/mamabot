"""Text normalization helpers shared by NLP components."""

from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("message must be text")
    normalized = unicodedata.normalize("NFKC", text)
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.category(character).startswith("C")
        or character in {"\n", "\r", "\t"}
    )
    return re.sub(r"\s+", " ", normalized).strip()
