"""Provider-independent WhatsApp boundary.

No vendor-specific WhatsApp API documentation is included in this repository.
The real provider therefore receives explicit transport and signature hooks;
no endpoint, payload, credential, or webhook contract is guessed here.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from utils.validators import validate_message

from .base import InboundMessage, OutboundMessage

log = logging.getLogger(__name__)


class WhatsAppConfigurationError(RuntimeError):
    """Raised when the documented provider transport is not configured."""


class WhatsAppDeliveryError(RuntimeError):
    """Raised when the configured provider rejects an outbound message."""


@dataclass(frozen=True)
class WhatsAppSendRequest:
    recipient: str
    text: str
    access_token: str
    phone_number_id: str


SendTransport = Callable[[WhatsAppSendRequest], Any]
SignatureVerifier = Callable[[bytes, str | None], bool]


@dataclass
class WhatsAppProvider:
    """Real-provider boundary with credentials and transport supplied externally."""

    access_token: str
    phone_number_id: str = ""
    send_transport: SendTransport | None = None
    signature_verifier: SignatureVerifier | None = None
    channel: str = "whatsapp"

    def normalize_inbound(self, payload: Any) -> InboundMessage:
        if not isinstance(payload, Mapping):
            raise TypeError("WhatsApp payload must be an object")
        text = validate_message(payload.get("message", ""))
        sender = str(payload.get("from", "")).strip()
        if not sender:
            raise ValueError("WhatsApp sender is required")
        return InboundMessage(sender, text, self.channel, dict(payload))

    def verify_request(self, raw_body: bytes, signature: str | None) -> bool:
        if self.signature_verifier is None:
            raise WhatsAppConfigurationError(
                "WhatsApp signature verifier is not configured from provider documentation"
            )
        return bool(self.signature_verifier(raw_body, signature))

    def send(self, recipient: str, text: str) -> OutboundMessage:
        if not self.access_token or not self.phone_number_id:
            raise WhatsAppConfigurationError("WhatsApp credentials are not configured")
        if not recipient or not text.strip():
            raise ValueError("recipient and text are required")
        if self.send_transport is None:
            raise WhatsAppConfigurationError(
                "WhatsApp send transport is not configured from provider documentation"
            )
        request = WhatsAppSendRequest(
            recipient, text, self.access_token, self.phone_number_id
        )
        try:
            self.send_transport(request)
        except Exception as exc:
            log.exception("WhatsApp delivery failed for recipient=%s", recipient)
            raise WhatsAppDeliveryError("WhatsApp delivery failed") from exc
        log.info("WhatsApp message accepted for recipient=%s", recipient)
        return OutboundMessage(recipient, text, self.channel)


@dataclass
class MockWhatsAppProvider:
    """Credential-free provider used by local development and automated tests."""

    channel: str = "whatsapp"
    sent: list[OutboundMessage] | None = None
    valid_signature: bool = True

    def __post_init__(self) -> None:
        if self.sent is None:
            self.sent = []

    def normalize_inbound(self, payload: Any) -> InboundMessage:
        if not isinstance(payload, Mapping):
            raise TypeError("WhatsApp payload must be an object")
        text = validate_message(payload.get("message", ""))
        sender = str(payload.get("from", "")).strip()
        if not sender:
            raise ValueError("WhatsApp sender is required")
        return InboundMessage(sender, text, self.channel, dict(payload))

    def verify_request(self, raw_body: bytes, signature: str | None) -> bool:
        return self.valid_signature

    def send(self, recipient: str, text: str) -> OutboundMessage:
        if not recipient or not text.strip():
            raise ValueError("recipient and text are required")
        message = OutboundMessage(recipient, text, self.channel)
        self.sent.append(message)
        return message
