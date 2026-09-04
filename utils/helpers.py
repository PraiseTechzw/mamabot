"""Small shared helpers."""
def mask_phone(phone: str) -> str: return phone[:3] + "****" + phone[-2:] if len(phone) > 5 else "***"
