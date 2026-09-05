"""Named conversation flows for callers that want explicit routing."""

from .manager import DialogueManager


def handle_message(
    manager: DialogueManager,
    text: str,
    phone_number: str = "local-user",
    language: str = "en",
    channel: str = "browser",
):
    """Process one transport-neutral inbound message."""
    return manager.respond(text, phone_number, language, channel)
