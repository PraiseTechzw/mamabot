import unittest

from app.routes.webhook import _sms_format
from app.services.clinical_safety import SAFETY_NOTICE, with_safety_notice


class ClinicalSafetyTests(unittest.TestCase):
    def test_safety_notice_is_added_once(self):
        response = with_safety_notice("Health information")

        self.assertEqual(response, f"Health information\n\n{SAFETY_NOTICE}")
        self.assertEqual(with_safety_notice(response), response)

    def test_sms_truncation_preserves_notice_within_limit(self):
        response = _sms_format("Health information. " * 100, include_safety_notice=True)

        self.assertLessEqual(len(response), 459)
        self.assertTrue(response.endswith(SAFETY_NOTICE))
        self.assertIn("Reply 1-7 for topics.", response)


if __name__ == "__main__":
    unittest.main()
