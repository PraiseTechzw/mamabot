import unittest
from unittest.mock import patch

from app import create_app
from config import ProductionConfig, validate_production_config


class ProductionConfigTests(unittest.TestCase):
    def setUp(self):
        self.valid_config = {
            "SECRET_KEY": "s" * 32,
            "ADMIN_PASSWORD": "secure-admin-password",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_KEY": "service-role-key",
        }

    def test_core_production_settings_are_accepted(self):
        validate_production_config(self.valid_config)

    def test_production_app_refuses_missing_configuration(self):
        with patch.multiple(
            ProductionConfig,
            SECRET_KEY="",
            ADMIN_PASSWORD="",
            SUPABASE_URL="",
            SUPABASE_KEY="",
            SMSPOP_API_TOKEN=None,
            SMSPOP_SENDER_ID=None,
            SMSPOP_DELIVERY_REPORT_URL=None,
            SMSPOP_WEBHOOK_SECRET=None,
            TWILIO_ACCOUNT_SID=None,
            TWILIO_AUTH_TOKEN=None,
            TWILIO_WHATSAPP_NUMBER=None,
            TWILIO_WHATSAPP_REMINDER_CONTENT_SID=None,
        ):
            with self.assertRaisesRegex(RuntimeError, "SECRET_KEY must be configured"):
                create_app("production")

    def test_example_supabase_credentials_are_rejected(self):
        config = {
            **self.valid_config,
            "SUPABASE_URL": "https://your-project.supabase.co",
            "SUPABASE_KEY": "server-side-service-role-key",
        }

        with self.assertRaisesRegex(RuntimeError, "SUPABASE_URL must not use a placeholder"):
            validate_production_config(config)

    def test_required_settings_must_be_present(self):
        config = {**self.valid_config, "SUPABASE_KEY": ""}

        with self.assertRaisesRegex(RuntimeError, "SUPABASE_KEY must be configured"):
            validate_production_config(config)

    def test_partial_provider_configuration_is_rejected(self):
        config = {**self.valid_config, "TWILIO_WHATSAPP_NUMBER": "whatsapp:+263771234567"}

        with self.assertRaisesRegex(
            RuntimeError,
            "TWILIO_ACCOUNT_SID is required when Twilio WhatsApp reminders are enabled",
        ):
            validate_production_config(config)

    def test_inbound_twilio_auth_does_not_require_reminder_configuration(self):
        config = {**self.valid_config, "TWILIO_AUTH_TOKEN": "webhook-auth-token"}

        validate_production_config(config)

    def test_partial_twilio_reminder_config_is_rejected(self):
        config = {**self.valid_config, "TWILIO_WHATSAPP_NUMBER": "whatsapp:+263771234567"}

        with self.assertRaisesRegex(
            RuntimeError,
            "TWILIO_AUTH_TOKEN is required when Twilio WhatsApp reminders are enabled",
        ):
            validate_production_config(config)

    def test_delivery_reports_require_a_signing_secret(self):
        config = {
            **self.valid_config,
            "SMSPOP_DELIVERY_REPORT_URL": "https://example.test/webhook",
        }

        with self.assertRaisesRegex(
            RuntimeError,
            "SMSPOP_WEBHOOK_SECRET is required when delivery reports are enabled",
        ):
            validate_production_config(config)

    def test_weak_admin_password_is_rejected(self):
        config = {**self.valid_config, "ADMIN_PASSWORD": "short"}

        with self.assertRaisesRegex(RuntimeError, "at least 12 characters"):
            validate_production_config(config)


if __name__ == "__main__":
    unittest.main()
