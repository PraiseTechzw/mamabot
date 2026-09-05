from datetime import datetime, timezone
from pathlib import Path

from database.models import ConversationMessage
from database.queries import InMemoryRepository

ROOT = Path(__file__).resolve().parents[1]


def test_repository_saves_and_retrieves_conversation_messages():
    repository = InMemoryRepository()
    user = repository.get_or_create_user("0771234567")

    saved = repository.save_message(
        ConversationMessage(
            None,
            user.id,
            "test",
            "inbound",
            "Hello MamaBot",
            datetime.now(timezone.utc),
        )
    )
    repository.save_message(
        ConversationMessage(
            None,
            user.id,
            "test",
            "outbound",
            "Hello, how can I help?",
            datetime.now(timezone.utc),
            saved.conversation_id,
        )
    )

    messages = repository.list_messages(saved.conversation_id or 0)
    assert [message.text for message in messages] == [
        "Hello MamaBot",
        "Hello, how can I help?",
    ]
    assert messages[0].conversation_id == messages[1].conversation_id


def test_database_scripts_cover_required_relational_entities():
    schema = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    seed = (ROOT / "sql" / "seed.sql").read_text(encoding="utf-8")

    for table in (
        "users",
        "pregnancy_profiles",
        "appointments",
        "conversations",
        "messages",
        "reminders",
        "health_workers",
        "escalations",
        "supported_languages",
        "communication_channels",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema
    assert "0770000000" in seed
