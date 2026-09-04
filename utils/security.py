"""Security helpers for webhook verification."""
import hmac


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    return bool(secret) and hmac.compare_digest(signature, hmac.new(secret.encode(), payload, "sha256").hexdigest())
