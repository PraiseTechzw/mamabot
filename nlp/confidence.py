"""Confidence thresholds used for safe response selection."""
HIGH_CONFIDENCE = 0.62
LOW_CONFIDENCE = 0.40

def is_confident(confidence: float) -> bool:
    return confidence >= HIGH_CONFIDENCE
