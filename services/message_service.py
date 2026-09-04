"""Transport-neutral message service."""
from dialogue.manager import DialogueManager


class MessageService:
    def __init__(self, manager: DialogueManager): self.manager = manager
    def handle(self, text: str, sender: str, channel: str = "browser", language: str = "en"): return self.manager.respond(text, sender, language, channel)
