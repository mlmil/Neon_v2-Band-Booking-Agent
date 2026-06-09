import unittest

ALLOWED_STATUSES = {"success", "needs_review", "blocked", "failed", "uncertain"}
PROTECTED_WRITES = {
    "calendar_update",
    "bandsheet_publish",
    "venue_email_send",
    "portal_share",
    "payment_complete",
    "booking_confirmed",
    "rate_change",
}


def can_perform_protected_write(lane_status):
    return lane_status == "success"


class FailureStatusTests(unittest.TestCase):
    def test_allowed_statuses_include_blocking_states(self):
        self.assertIn("blocked", ALLOWED_STATUSES)
        self.assertIn("uncertain", ALLOWED_STATUSES)

    def test_protected_writes_stop_when_uncertain(self):
        for status in ["needs_review", "blocked", "failed", "uncertain"]:
            self.assertFalse(can_perform_protected_write(status))

    def test_protected_writes_continue_only_on_success(self):
        self.assertTrue(can_perform_protected_write("success"))
        self.assertIn("bandsheet_publish", PROTECTED_WRITES)


if __name__ == "__main__":
    unittest.main()
