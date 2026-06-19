import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from telegram_bot.providers.closeout import CloseoutQueueProvider


class CloseoutQueueProviderTests(unittest.TestCase):
    def test_reads_needs_closeout_rows(self) -> None:
        with TemporaryDirectory() as temp_dir:
            queue = Path(temp_dir) / "queue.csv"
            queue.write_text(
                "gig_id,venue,city,date,start_at,end_at,queue_status,next_step,created_at,updated_at\n"
                '1,Tony\'s Pizza,Ventura,2026-06-06,2026-06-06T19:00:00-07:00,,needs_closeout,"Ask Mike for pay.",,\n'
                "2,Leashless,Ventura,2026-07-19,2026-07-19T15:00:00-07:00,,scheduled,Wait until the show ends.,,\n",
                encoding="utf-8",
            )

            rows = CloseoutQueueProvider(queue).needs_closeout(limit=5)

        self.assertEqual(rows, ["2026-06-06 - Tony's Pizza (Ventura): Ask Mike for pay."])


if __name__ == "__main__":
    unittest.main()
