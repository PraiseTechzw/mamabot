from app import create_app
from database.queries import InMemoryRepository


def test_local_test_webhook_uses_shared_dialogue_and_persists_messages():
    repository = InMemoryRepository()
    app = create_app({"TESTING": True, "MAMABOT_REPOSITORY": repository})
    client = app.test_client()

    response = client.post(
        "/webhook/test",
        json={"message": "Hello MamaBot", "sender": "0771234567"},
    )

    assert response.status_code == 200
    assert response.get_json()["text"]
    assert [message.direction for message in repository.messages] == [
        "inbound",
        "outbound",
    ]


def test_local_test_webhook_returns_validation_errors():
    client = create_app({"TESTING": True}).test_client()

    response = client.post("/webhook/test", json={"message": " "})

    assert response.status_code == 400
    assert "error" in response.get_json()
