import hashlib
import hmac
import json
import time
import unittest
from unittest.mock import patch

from app import create_app
from twilio.request_validator import RequestValidator


class ApplicationRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("development")
        self.app.config.update(
            TESTING=True,
            SMSPOP_WEBHOOK_SECRET="test-webhook-secret",
            TWILIO_AUTH_TOKEN="test-twilio-auth-token",
        )
        self.client = self.app.test_client()

    def test_admin_api_requires_login(self):
        response = self.client.post("/admin/patients", json={"consent": True})
        self.assertEqual(response.status_code, 401)

    @patch("app.routes.webhook.process_message", return_value="Reply")
    def test_twilio_webhook_accepts_valid_signature(self, process_message):
        form = {"Body": "hello", "From": "whatsapp:+263771234567"}
        url = "http://localhost/webhook/twilio"
        signature = RequestValidator(
            self.app.config["TWILIO_AUTH_TOKEN"]
        ).compute_signature(url, form)

        response = self.client.post(
            "/webhook/twilio",
            data=form,
            headers={"X-Twilio-Signature": signature},
        )

        self.assertEqual(response.status_code, 200)
        process_message.assert_called_once_with(
            "hello",
            "whatsapp:+263771234567",
            "whatsapp",
        )

    @patch("app.routes.webhook.process_message")
    def test_twilio_webhook_rejects_invalid_signature(self, process_message):
        response = self.client.post(
            "/webhook/sms",
            data={"Body": "hello", "From": "+263771234567"},
            headers={"X-Twilio-Signature": "invalid"},
        )

        self.assertEqual(response.status_code, 403)
        process_message.assert_not_called()

    def test_twilio_webhook_requires_configured_auth_token(self):
        self.app.config["TWILIO_AUTH_TOKEN"] = None

        response = self.client.post("/webhook/twilio")

        self.assertEqual(response.status_code, 503)

    @patch("app.routes.webhook.process_message", return_value="Reply")
    def test_twilio_webhook_uses_configured_public_base_url(self, process_message):
        self.app.config["TWILIO_WEBHOOK_BASE_URL"] = "https://bot.example.test"
        form = {"Body": "hello", "From": "+263771234567"}
        url = "https://bot.example.test/webhook/twilio?source=provider"
        signature = RequestValidator(
            self.app.config["TWILIO_AUTH_TOKEN"]
        ).compute_signature(url, form)

        response = self.client.post(
            "/webhook/twilio?source=provider",
            data=form,
            headers={"X-Twilio-Signature": signature},
        )

        self.assertEqual(response.status_code, 200)
        process_message.assert_called_once()

    @patch("app.db.test_connection", return_value=(True, "Connected (Supabase REST)"))
    def test_readiness_endpoint_reports_database_connection(self, test_connection):
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"status": "ok", "checks": {"database": "ok"}},
        )
        test_connection.assert_called_once_with()

    @patch("app.db.test_connection", return_value=(False, "Database unavailable"))
    def test_readiness_endpoint_returns_service_unavailable_without_database(
        self, test_connection
    ):
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.get_json(),
            {"status": "not_ready", "checks": {"database": "not_ready"}},
        )
        test_connection.assert_called_once_with()

    @patch("app.routes.smspop.db.save_sms_delivery_report")
    def test_sms_pop_delivery_report_is_verified_and_persisted(self, save_report):
        timestamp = str(int(time.time()))
        report = {
            "event": "message.delivery_report",
            "webhook_id": 101,
            "message_id": 201,
            "phone": "263771234567",
            "status": "delivered",
        }
        raw_body = json.dumps(report, separators=(",", ":")).encode()
        digest = hmac.new(
            b"test-webhook-secret",
            timestamp.encode() + b"." + raw_body,
            hashlib.sha256,
        ).hexdigest()

        response = self.client.post(
            "/webhook/smspop/delivery-reports",
            data=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-SmsPop-Event": report["event"],
                "X-SmsPop-Timestamp": timestamp,
                "X-SmsPop-Signature": f"sha256={digest}",
            },
        )

        self.assertEqual(response.status_code, 200)
        save_report.assert_called_once_with(report)

    def test_sms_pop_delivery_report_rejects_bad_signature(self):
        response = self.client.post(
            "/webhook/smspop/delivery-reports",
            data=b'{"event":"webhook.test"}',
            headers={
                "Content-Type": "application/json",
                "X-SmsPop-Event": "webhook.test",
                "X-SmsPop-Timestamp": str(int(time.time())),
                "X-SmsPop-Signature": "sha256=invalid",
            },
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
