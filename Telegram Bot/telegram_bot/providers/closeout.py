import csv
from pathlib import Path

DEFAULT_QUEUE_PATH = Path("/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/data/post_gig/queue.csv")


class CloseoutQueueProvider:
    def __init__(self, queue_path: Path = DEFAULT_QUEUE_PATH) -> None:
        self._queue_path = queue_path

    def needs_closeout(self, *, limit: int = 5) -> list[str]:
        if not self._queue_path.exists():
            return []
        with self._queue_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        items: list[str] = []
        for row in rows:
            if row.get("queue_status") != "needs_closeout":
                continue
            venue = row.get("venue") or "Unknown venue"
            city = row.get("city") or "Unknown city"
            date = row.get("date") or "Unknown date"
            next_step = row.get("next_step") or "Needs closeout details."
            items.append(f"{date} - {venue} ({city}): {next_step}")
        return items[:limit]
