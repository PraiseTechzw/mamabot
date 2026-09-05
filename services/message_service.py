"""Transport-neutral message service."""

from database.models import ConversationMessage
from dialogue.manager import DialogueManager


class MessageService:
    def __init__(self, manager: DialogueManager):
        self.manager = manager
        self.repository = manager.repository

    def handle(
        self, text: str, sender: str, channel: str = "browser", language: str = "en"
    ):
        return self.manager.respond(text, sender, language, channel)

    def save(self, message: ConversationMessage):
        return self.repository.save_message(message)

    def list_messages(self, conversation_id: int, limit: int = 100):
        return self.repository.list_messages(conversation_id, limit)
