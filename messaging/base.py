"""Provider-independent messaging interfaces."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OutboundMessage:
    recipient: str
    text: str
    channel: str

class MessageProvider(Protocol):
    channel: str
    def send(self, recipient: str, text: str) -> OutboundMessage: ...
