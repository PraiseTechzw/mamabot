"""Provider-independent WhatsApp boundary.

A concrete vendor adapter can implement this interface later without changing
MamaBot's dialogue, NLP, or service layers.
"""
from __future__ import annotations

from .base import OutboundMessage


class WhatsAppProvider:
    channel = "whatsapp"
    def send(self, recipient: str, text: str) -> OutboundMessage:
        raise NotImplementedError("Connect a WhatsApp provider adapter before enabling WhatsApp")

class ConsoleWhatsAppProvider(WhatsAppProvider):
    """Local no-credential adapter; useful for development and manual testing."""
    def send(self, recipient: str, text: str) -> OutboundMessage:
        return OutboundMessage(recipient, text, self.channel)
