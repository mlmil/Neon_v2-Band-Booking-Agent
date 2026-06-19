import unittest

from telegram_bot.booking_watcher.detector import detect_booking_signal


class BookingDetectorTests(unittest.TestCase):
    def test_detects_cancellation_with_date_as_high_priority(self) -> None:
        signal = detect_booking_signal("Kyle said the June 27 party is canceled")

        self.assertIsNotNone(signal)
        assert signal is not None
        self.assertEqual(signal.signal_type, "cancellation")
        self.assertEqual(signal.priority, "high")
        self.assertEqual(signal.extracted_date, "June 27")

    def test_detects_confirmed_booking_as_high_priority(self) -> None:
        signal = detect_booking_signal("Alfred booked us at Leashless on July 12")

        self.assertIsNotNone(signal)
        assert signal is not None
        self.assertEqual(signal.signal_type, "new_booking")
        self.assertEqual(signal.priority, "high")
        self.assertEqual(signal.extracted_date, "July 12")

    def test_detects_vague_hold_as_normal_priority(self) -> None:
        signal = detect_booking_signal("Can we hold August 9 for that party?")

        self.assertIsNotNone(signal)
        assert signal is not None
        self.assertEqual(signal.signal_type, "hold_or_tentative")
        self.assertEqual(signal.priority, "normal")
        self.assertEqual(signal.extracted_date, "August 9")

    def test_ordinary_chatter_is_ignored(self) -> None:
        self.assertIsNone(detect_booking_signal("That last set felt great."))


if __name__ == "__main__":
    unittest.main()
