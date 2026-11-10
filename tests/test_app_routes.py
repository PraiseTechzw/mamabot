import hashlib
import hmac
import json
import time
import unittest
from unittest.mock import patch

from app import create_app


class ApplicationRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("development")
        self.app.config.update(
            TESTING=True,
            SMSPOP_WEBHOOK_SECRET="test-webhook-secret",
        )
        self.client = self.app.test_client()

    def test_admin_api_requires_login(self):
        response = self.client.post("/admin/patients", json={"consent": True})
        self.assertEqual(response.status_code, 401)

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
