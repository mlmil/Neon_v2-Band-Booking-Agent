import subprocess
import shutil
from pathlib import Path

from telegram_bot.models import BandSheetSnapshot


class GeminiQuestionAnswerer:
    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        command: tuple[str, ...] | None = None,
        timeout_seconds: int = 45,
    ) -> None:
        self._repo_root = repo_root or Path(__file__).resolve().parents[3]
        self._command = command or resolve_gemini_command()
        self._timeout_seconds = timeout_seconds

    def __call__(self, question: str, snapshot: BandSheetSnapshot) -> str:
        completed = subprocess.run(
            [
                *self._command,
                "--skip-trust",
                "--approval-mode",
                "plan",
                "--prompt",
                self._build_prompt(question, snapshot),
            ],
            cwd=self._repo_root,
            text=True,
            capture_output=True,
            timeout=self._timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("Gemini read-only answer failed")
        answer = _clean_answer(completed.stdout)
        if not answer:
            raise RuntimeError("Gemini returned an empty answer")
        return answer

    def _build_prompt(self, question: str, snapshot: BandSheetSnapshot) -> str:
        lines = [
            "You are Neon V2 answering a Telegram question for Neon Blonde band members.",
            "Use only the provided Band Sheet snapshot and Neon V2 repo instructions.",
            "Read-only mode: do not send email, edit calendar, publish Band Sheet, update WordPress, or mark payments.",
            "If the snapshot does not contain enough information, say what cannot be verified and suggest a fixed command such as /gigs, /status, /free, or /venue <name>.",
            "Keep the answer short, plain, and useful for a band chat.",
            "",
            f"Question: {question}",
            "",
            "Band Sheet source:",
            f"- Updated: {snapshot.source.updated_at.date().isoformat()}",
            f"- Freshness days: {snapshot.source.freshness_days}",
            f"- Stale: {snapshot.source.is_stale}",
            "",
            "Upcoming gigs:",
        ]
        if snapshot.booked_gigs:
            for gig in snapshot.booked_gigs:
                date = gig.date or "date unknown"
                time = gig.start_time or "time unknown"
                venue = gig.venue_name or gig.summary
                city = f" ({gig.city})" if gig.city else ""
                lines.append(f"- {date} @ {time} - {venue}{city}")
        else:
            lines.append("- None found.")

        lines.append("")
        lines.append("Member availability notes:")
        lines.extend(snapshot.members_out or ["- None found."])

        lines.append("")
        lines.append("Open dates from Band Sheet:")
        lines.extend(snapshot.free_weekends or ["- None found."])

        lines.append("")
        lines.append("This week:")
        lines.extend(snapshot.this_week or ["- None found."])
        return "\n".join(lines)


def _clean_answer(raw: str) -> str:
    lines = [line.rstrip() for line in raw.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def resolve_gemini_command() -> tuple[str, ...]:
    path_command = shutil.which("gemini")
    if path_command:
        return (path_command,)
    return ("/opt/homebrew/bin/gemini",)
