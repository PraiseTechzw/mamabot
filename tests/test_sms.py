import pytest

from app import create_app
from database.queries import InMemoryRepository
from messaging.sms_provider import (
    MockSmsPopProvider,
    SmsPopConfigurationError,
    SmsPopDeliveryError,
    SmsPopProvider,
    SmsPopSendRequest,
)


def test_mock_sms_provider_sends_without_credentials():
    provider = MockSmsPopProvider()

    message = provider.send("0771234567", "Hello from MamaBot")

    assert message.recipient == "0771234567"
    assert message.channel == "sms"
    assert provider.sent == [message]


def test_sms_provider_normalizes_internal_inbound_payload():
    provider = MockSmsPopProvider()

    message = provider.normalize_inbound({"from": "0771234567", "message": "Hello"})

    assert message.sender == "0771234567"
    assert message.text == "Hello"
    assert message.channel == "sms"


def test_sms_provider_requires_documented_transport_hook():
    provider = SmsPopProvider(api_key="mock-key")

    with pytest.raises(SmsPopConfigurationError, match="transport"):
        provider.send("0771234567", "Hello")


def test_sms_provider_uses_injected_transport_without_exposing_secret():
    requests: list[SmsPopSendRequest] = []

    def transport(request: SmsPopSendRequest):
        requests.append(request)
        return {"accepted": True}

    provider = SmsPopProvider("mock-key", sender_id="MamaBot", send_transport=transport)
    message = provider.send("0771234567", "Hello")

    assert message.channel == "sms"
    assert requests == [SmsPopSendRequest("0771234567", "Hello", "MamaBot")]
    assert "mock-key" not in repr(requests)


def test_sms_provider_wraps_transport_failures():
    def transport(_request):
        raise RuntimeError("vendor failure")

    provider = SmsPopProvider("mock-key", send_transport=transport)

    with pytest.raises(SmsPopDeliveryError, match="delivery failed"):
        provider.send("0771234567", "Hello")


def test_sms_webhook_uses_shared_dialogue_and_provider():
    repository = InMemoryRepository()
    provider = MockSmsPopProvider()
    app = create_app(
        {
            "TESTING": True,
            "MAMABOT_REPOSITORY": repository,
            "SMS_PROVIDER": provider,
        }
    )

    response = app.test_client().post(
        "/sms/inbound",
        json={"from": "0771234567", "message": "Hello MamaBot"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["channel"] == "sms"
    assert payload["intent"] == "general_greeting"
    assert len(provider.sent) == 1
    assert len(repository.messages) == 2


def test_sms_webhook_rejects_invalid_payload_without_provider_call():
    provider = MockSmsPopProvider()
    app = create_app({"TESTING": True, "SMS_PROVIDER": provider})

    response = app.test_client().post("/sms/inbound", json={"from": "0771234567"})

    assert response.status_code == 400
    assert provider.sent == []
