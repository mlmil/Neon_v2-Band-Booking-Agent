from pathlib import Path

from telegram_bot.config import EXPECTED_LANE_NAME, REQUIRED_REPO_MARKERS, default_lane_root
from telegram_bot.models import RepoContext


class DiscoveryError(RuntimeError):
    """Raised when the Telegram bot lane is not in the expected repo layout."""


def discover_repo_context(lane_root: Path | None = None) -> RepoContext:
    resolved_lane_root = (lane_root or default_lane_root()).resolve()
    if resolved_lane_root.name != EXPECTED_LANE_NAME:
        raise DiscoveryError(f"Expected lane '{EXPECTED_LANE_NAME}', got '{resolved_lane_root.name}'")

    repo_root = resolved_lane_root.parent
    missing = [marker for marker in REQUIRED_REPO_MARKERS if not (repo_root / marker).exists()]
    if missing:
        raise DiscoveryError(f"Repo root is missing required markers: {', '.join(missing)}")

    return RepoContext(
        repo_root=repo_root,
        lane_root=resolved_lane_root,
        lane_name=resolved_lane_root.name,
    )
