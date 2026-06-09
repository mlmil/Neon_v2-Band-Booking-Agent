import csv
import tempfile
import unittest
from pathlib import Path

from scripts.scout_agent_tool import REQUIRED_COLUMNS, validate_scout_csv


class ScoutAgentToolTests(unittest.TestCase):
    def test_valid_empty_csv_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scout-leads.csv"
            path.write_text(",".join(REQUIRED_COLUMNS) + "\n")
            result = validate_scout_csv(path)
            self.assertEqual(result["status"], "success")

    def test_missing_column_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scout-leads.csv"
            path.write_text("lead_id,venue_name,status\n")
            result = validate_scout_csv(path)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["code"], "SCOUT_SOURCE_INCOMPLETE")

    def test_invalid_status_needs_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scout-leads.csv"
            with path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                row = {column: "" for column in REQUIRED_COLUMNS}
                row["lead_id"] = "lead-1"
                row["venue_name"] = "Example Room"
                row["status"] = "maybe"
                writer.writerow(row)
            result = validate_scout_csv(path)
            self.assertEqual(result["status"], "needs_review")
            self.assertIn("maybe", result["failure_reason"])


if __name__ == "__main__":
    unittest.main()
