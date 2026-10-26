import unittest

from src.legal_sms import Matter, build_campaign


class CampaignDecisionTest(unittest.TestCase):
    def test_each_matter_gets_a_due_date_message_and_stable_retry_key(self) -> None:
        matter = Matter("MAT-7", "+15550007", "Avery", "signed document delivery", "2026-12-01")
        message = build_campaign([matter])[0]
        self.assertIn("signed document delivery", message.text)
        self.assertIn("2026-12-01", message.text)
        self.assertEqual(message.idempotency_key, "matter-MAT-7")


if __name__ == "__main__":
    unittest.main()
