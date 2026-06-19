from pathlib import Path

BANDSHEET_PAGE_URL = "https://mlmil.github.io/NeonBlonde-Bandsheet/docs/"
BANDSHEET_JSON_URL = "https://mlmil.github.io/NeonBlonde-Bandsheet/docs/bandsheet-data.json"
BANDSHEET_STALE_AFTER_DAYS = 4
HTTP_TIMEOUT_SECONDS = 10
EXPECTED_LANE_NAME = "Telegram Bot"
REQUIRED_REPO_MARKERS = ("SKILL.md", "README.md")


def default_lane_root() -> Path:
    return Path(__file__).resolve().parents[1]
