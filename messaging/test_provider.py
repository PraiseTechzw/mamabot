"""In-memory provider used by local browser tests and automated tests."""
from __future__ import annotations

from dataclasses import dataclass, field

from .base import OutboundMessage


@dataclass
class TestMessageProvider:
    __test__ = False
    channel: str = "test"
    sent: list[OutboundMessage] = field(default_factory=list)
    def send(self, recipient: str, text: str) -> OutboundMessage:
        message = OutboundMessage(recipient, text, self.channel)
        self.sent.append(message)
        return message
