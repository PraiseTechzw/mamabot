import hashlib
import hmac
import json
import unittest
from unittest.mock import Mock, patch

from flask import Flask

from app.services.messaging import (
    SMSPOP_API_URL,
    send_sms,
    verify_smspop_signature,
)


class MessagingTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SMSPOP_API_TOKEN="test-token",
            SMSPOP_SENDER_ID="MAMABOT",
            SMSPOP_DELIVERY_REPORT_URL="https://example.test/webhook",
        )

    @patch("app.services.messaging.requests.post")
    def test_sms_pop_campaign_uses_documented_payload(self, post):
        response = Mock()
        response.json.return_value = {
            "success": True,
            "data": {"contacts": [{"message_id": 123, "status": "sent"}]},
        }
        post.return_value = response

        with self.app.app_context():
            result = send_sms("+263771234567", "MamaBot reminder")

        self.assertEqual(result.message_id, "123")
        self.assertEqual(result.status, "accepted")
        self.assertEqual(post.call_args.args[0], SMSPOP_API_URL)
        self.assertEqual(
            post.call_args.kwargs["json"],
            {
                "name": "MamaBot message",
                "message": "MamaBot reminder",
                "sender_id": "MAMABOT",
                "contact_import_method": "manual",
                "manual_contacts": "+263771234567",
                "callback_url": "https://example.test/webhook",
            },
        )
        self.assertEqual(
            post.call_args.kwargs["headers"]["Authorization"],
            "Bearer test-token",
        )

    def test_sms_rejects_non_e164_numbers(self):
        with self.app.app_context(), self.assertRaises(ValueError):
            send_sms("0771234567", "MamaBot reminder")

    def test_sms_rejects_missing_provider_configuration(self):
        self.app.config["SMSPOP_API_TOKEN"] = None
        with self.app.app_context(), self.assertRaisesRegex(RuntimeError, "SMSPOP_API_TOKEN"):
            send_sms("+263771234567", "MamaBot reminder")

    def test_smspop_signature_accepts_fresh_signed_raw_body(self):
        body = json.dumps({"event": "webhook.test"}).encode()
        timestamp = "1794330000"
        secret = "local-test-secret"
        digest = hmac.new(
            secret.encode(),
            timestamp.encode() + b"." + body,
            hashlib.sha256,
        ).hexdigest()

        self.assertTrue(
            verify_smspop_signature(
                body,
                timestamp,
                f"sha256={digest}",
                secret,
                now=1794330000,
            )
        )
        self.assertFalse(
            verify_smspop_signature(
                body,
                timestamp,
                f"sha256={digest}",
                secret,
                now=1794330301,
            )
        )


if __name__ == "__main__":
    unittest.main()
