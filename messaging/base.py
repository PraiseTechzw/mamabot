"""Provider-independent messaging interfaces."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class OutboundMessage:
    recipient: str
    text: str
    channel: str


@dataclass(frozen=True)
class InboundMessage:
    sender: str
    text: str
    channel: str
    metadata: dict[str, Any] | None = None


class MessageProvider(Protocol):
    channel: str
    def send(self, recipient: str, text: str) -> OutboundMessage: ...

    def normalize_inbound(self, payload: Any) -> InboundMessage: ...
