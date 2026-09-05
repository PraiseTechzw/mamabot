import pytest

from app import create_app
from database.queries import InMemoryRepository
from messaging.whatsapp_provider import (
    MockWhatsAppProvider,
    WhatsAppConfigurationError,
    WhatsAppDeliveryError,
    WhatsAppProvider,
    WhatsAppSendRequest,
)


def test_mock_whatsapp_provider_normalizes_and_sends():
    provider = MockWhatsAppProvider()
    inbound = provider.normalize_inbound({"from": "263771234567", "message": "Hello"})
    outbound = provider.send(inbound.sender, "Hello from MamaBot")

    assert inbound.sender == "263771234567"
    assert inbound.text == "Hello"
    assert inbound.channel == "whatsapp"
    assert provider.sent == [outbound]


def test_real_whatsapp_provider_requires_documented_transport_hooks():
    provider = WhatsAppProvider(access_token="token", phone_number_id="number-id")

    with pytest.raises(WhatsAppConfigurationError, match="signature"):
        provider.verify_request(b"{}", None)
    with pytest.raises(WhatsAppConfigurationError, match="transport"):
        provider.send("263771234567", "Hello")


def test_real_provider_uses_injected_transport_without_exposing_token():
    requests: list[WhatsAppSendRequest] = []

    def transport(request: WhatsAppSendRequest):
        requests.append(request)

    provider = WhatsAppProvider(
        "secret-token",
        "phone-id",
        send_transport=transport,
        signature_verifier=lambda body, signature: body == b"{}"
        and signature == "valid",
    )
    assert provider.verify_request(b"{}", "valid") is True
    message = provider.send("263771234567", "Hello")

    assert message.channel == "whatsapp"
    assert requests[0].recipient == "263771234567"
    assert requests[0].text == "Hello"
    assert requests[0].access_token == "secret-token"


def test_real_provider_wraps_transport_failure():
    def transport(_request):
        raise RuntimeError("vendor failure")

    provider = WhatsAppProvider("token", "phone", send_transport=transport)

    with pytest.raises(WhatsAppDeliveryError, match="delivery failed"):
        provider.send("263771234567", "Hello")


def test_whatsapp_webhook_uses_shared_mamabot_core():
    repository = InMemoryRepository()
    provider = MockWhatsAppProvider()
    app = create_app(
        {
            "TESTING": True,
            "MAMABOT_REPOSITORY": repository,
            "WHATSAPP_PROVIDER_INSTANCE": provider,
        }
    )

    response = app.test_client().post(
        "/whatsapp/webhook",
        json={"from": "263771234567", "message": "Hello MamaBot"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["channel"] == "whatsapp"
    assert payload["intent"] == "general_greeting"
    assert len(provider.sent) == 1
    assert len(repository.messages) == 2


def test_whatsapp_webhook_rejects_invalid_signature():
    provider = MockWhatsAppProvider(valid_signature=False)
    app = create_app({"TESTING": True, "WHATSAPP_PROVIDER_INSTANCE": provider})

    response = app.test_client().post(
        "/whatsapp/webhook",
        json={"from": "263771234567", "message": "Hello"},
    )

    assert response.status_code == 401
    assert provider.sent == []


def test_browser_chat_is_independent_of_whatsapp_provider():
    app = create_app(
        {"TESTING": True, "WHATSAPP_PROVIDER_INSTANCE": MockWhatsAppProvider()}
    )

    response = app.test_client().post("/api/chat", json={"message": "Hello MamaBot"})

    assert response.status_code == 200
    assert response.get_json()["intent"] == "general_greeting"
