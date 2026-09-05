"""Transport adapter for provider-independent WhatsApp webhooks."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from messaging.whatsapp_provider import (
    MockWhatsAppProvider,
    WhatsAppConfigurationError,
    WhatsAppDeliveryError,
)

log = logging.getLogger(__name__)


def register(service, provider=None):
    bp = Blueprint("whatsapp", __name__, url_prefix="/whatsapp")
    provider = provider or MockWhatsAppProvider()

    @bp.post("/webhook")
    def webhook():
        raw_body = request.get_data(cache=True)
        signature = request.headers.get("X-WhatsApp-Signature")
        try:
            if not provider.verify_request(raw_body, signature):
                return jsonify({"error": "Invalid WhatsApp webhook signature."}), 401
            payload = request.get_json(silent=True) or {}
            inbound = provider.normalize_inbound(payload)
        except (TypeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        except WhatsAppConfigurationError as exc:
            log.error("WhatsApp webhook is not configured: %s", exc)
            return jsonify({"error": "WhatsApp webhook is not configured."}), 503

        try:
            reply = service.handle(inbound.text, inbound.sender, inbound.channel)
            outbound = provider.send(inbound.sender, reply.text)
        except (
            WhatsAppConfigurationError,
            WhatsAppDeliveryError,
            ValueError,
            RuntimeError,
        ):
            log.exception("WhatsApp response could not be delivered")
            return (
                jsonify(
                    {"error": "The WhatsApp service could not deliver the response."}
                ),
                502,
            )
        return jsonify(
            {
                "recipient": outbound.recipient,
                "text": outbound.text,
                "channel": outbound.channel,
                "intent": reply.intent,
                "escalation": reply.escalation,
            }
        )

    return bp
