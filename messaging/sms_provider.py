"""SMSPOP integration boundary.

The repository does not contain SMSPOP's current API documentation. Therefore
this module deliberately does not guess an endpoint, authentication scheme, or
vendor payload. Configure an explicit transport callable built from the real
SMSPOP documentation when credentials and API details are available.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from utils.validators import validate_message

from .base import InboundMessage, OutboundMessage

log = logging.getLogger(__name__)


class SmsPopConfigurationError(RuntimeError):
    """Raised when undocumented SMSPOP transport details are not configured."""


class SmsPopDeliveryError(RuntimeError):
    """Raised when the configured SMSPOP transport rejects a message."""


@dataclass(frozen=True)
class SmsPopSendRequest:
    """Normalized data supplied to a documentation-specific transport hook."""

    recipient: str
    text: str
    sender_id: str


SendTransport = Callable[[SmsPopSendRequest], Any]


@dataclass
class SmsPopProvider:
    """Provider-neutral SMSPOP adapter with an explicit documentation hook."""

    api_key: str
    sender_id: str = "MamaBot"
    send_transport: SendTransport | None = None
    channel: str = "sms"

    def normalize_inbound(self, payload: Any) -> InboundMessage:
        """Normalize the project's canonical webhook payload.

        SMSPOP-specific field mapping must be performed by the deployment
        adapter after consulting its vendor documentation. The Flask route
        accepts only this internal shape: ``message`` and ``from``.
        """
        if not isinstance(payload, dict):
            raise TypeError("SMS payload must be an object")
        text = validate_message(payload.get("message", ""))
        sender = str(payload.get("from", "")).strip()
        if not sender:
            raise ValueError("SMS sender is required")
        return InboundMessage(sender, text, self.channel, dict(payload))

    def send(self, recipient: str, text: str) -> OutboundMessage:
        if not self.api_key:
            raise SmsPopConfigurationError("SMSPOP_API_KEY is not configured")
        if not recipient or not text.strip():
            raise ValueError("recipient and text are required")
        if self.send_transport is None:
            raise SmsPopConfigurationError(
                "SMSPOP send transport is not configured from the vendor documentation"
            )
        request = SmsPopSendRequest(recipient, text, self.sender_id)
        try:
            self.send_transport(request)
        except Exception as exc:
            log.exception("SMSPOP delivery failed for recipient=%s", recipient)
            raise SmsPopDeliveryError("SMSPOP delivery failed") from exc
        log.info("SMSPOP message accepted for recipient=%s", recipient)
        return OutboundMessage(recipient, text, self.channel)


@dataclass
class MockSmsPopProvider:
    """Credential-free provider for development and automated tests."""

    channel: str = "sms"
    sent: list[OutboundMessage] | None = None

    def __post_init__(self) -> None:
        if self.sent is None:
            self.sent = []

    def normalize_inbound(self, payload: Any) -> InboundMessage:
        if not isinstance(payload, dict):
            raise TypeError("SMS payload must be an object")
        text = validate_message(payload.get("message", ""))
        sender = str(payload.get("from", "")).strip()
        if not sender:
            raise ValueError("SMS sender is required")
        return InboundMessage(sender, text, self.channel, dict(payload))

    def send(self, recipient: str, text: str) -> OutboundMessage:
        if not recipient or not text.strip():
            raise ValueError("recipient and text are required")
        message = OutboundMessage(recipient, text, self.channel)
        self.sent.append(message)
        return message
