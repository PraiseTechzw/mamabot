from flask import Blueprint, jsonify, request

from messaging.sms_provider import (
    MockSmsPopProvider,
    SmsPopConfigurationError,
    SmsPopDeliveryError,
)


def register(service, provider=None):
    bp = Blueprint("sms", __name__, url_prefix="/sms")
    provider = provider or MockSmsPopProvider()

    @bp.post("/inbound")
    def inbound():
        data = request.get_json(silent=True) or request.form
        try:
            inbound = provider.normalize_inbound(dict(data))
        except (TypeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        try:
            reply = service.handle(inbound.text, inbound.sender, inbound.channel)
            outbound = provider.send(inbound.sender, reply.text)
        except (
            SmsPopConfigurationError,
            SmsPopDeliveryError,
            ValueError,
            RuntimeError,
        ):
            return (
                jsonify({"error": "The SMS service could not deliver the response."}),
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
