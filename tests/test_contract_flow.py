import unittest

from scripts.contract_flow import evaluate_contract_flow


class ContractFlowTests(unittest.TestCase):
    def test_signed_contract_with_test_payment_confirmed_waits_on_deposit(self):
        result = evaluate_contract_flow(
            {
                "signed_contract_received": True,
                "signed_contract_source": "gmail_attachment",
                "deposit_amount": 650,
                "deposit_received": False,
                "test_payment_requested": True,
                "test_payment_confirmed": True,
                "contract_time": "7:00 PM - 9:00 PM",
                "email_time": "8:00 PM - 10:00 PM",
            }
        )

        self.assertEqual(result["contract_status"], "signed_received")
        self.assertEqual(result["deposit_status"], "awaiting_deposit")
        self.assertEqual(result["next_follow_up_state"], "waiting_on_client_deposit")
        self.assertIn("TIME_MISMATCH_REVIEW", result["review_codes"])
        self.assertFalse(result["is_locked_for_accounting"])

    def test_deposit_received_locks_booking_money_state(self):
        result = evaluate_contract_flow(
            {
                "signed_contract_received": True,
                "deposit_amount": 650,
                "deposit_received": True,
                "test_payment_requested": True,
                "test_payment_confirmed": True,
                "contract_time": "8:00 PM - 10:00 PM",
                "email_time": "8:00 PM - 10:00 PM",
            }
        )

        self.assertEqual(result["deposit_status"], "deposit_received")
        self.assertEqual(result["next_follow_up_state"], "return_fully_signed_copy")
        self.assertTrue(result["is_locked_for_accounting"])
        self.assertEqual(result["review_codes"], [])


if __name__ == "__main__":
    unittest.main()
