"""SMSPOP adapter. It is inert until credentials are configured."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from .base import OutboundMessage

log = logging.getLogger(__name__)

@dataclass
class SmsPopProvider:
    base_url: str
    api_key: str
    sender_id: str = "MamaBot"
    timeout: float = 10.0
    channel: str = "sms"
    def send(self, recipient: str, text: str) -> OutboundMessage:
        if not self.api_key:
            raise RuntimeError("SMSPOP_API_KEY is not configured")
        if not recipient or not text.strip():
            raise ValueError("recipient and text are required")
        response = requests.post(
            self.base_url.rstrip("/") + "/sms/send",
            json={"to": recipient, "message": text, "from": self.sender_id},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return OutboundMessage(recipient, text, self.channel)
