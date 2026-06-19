import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PENDING_APPROVALS_PATH = Path.home() / ".hermes" / "neon_pending_approvals.json"


@dataclass(frozen=True)
class PendingDraft:
    to: list[str]
    from_name: str
    subject: str
    body: str


class PendingDraftsProvider:
    def __init__(self, path: Path = DEFAULT_PENDING_APPROVALS_PATH) -> None:
        self.path = path

    def list_drafts(self) -> list[PendingDraft]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        replies = payload.get("replies") if isinstance(payload, dict) else None
        if not isinstance(replies, list):
            return []

        drafts: list[PendingDraft] = []
        for reply in replies:
            if not isinstance(reply, dict):
                continue
            recipients = reply.get("to")
            to = [value for value in recipients if isinstance(value, str)] if isinstance(recipients, list) else []
            subject = reply.get("subject")
            body = reply.get("body")
            from_name = reply.get("from_name")
            if not isinstance(subject, str) or not isinstance(body, str):
                continue
            drafts.append(
                PendingDraft(
                    to=to,
                    from_name=from_name if isinstance(from_name, str) else "",
                    subject=subject,
                    body=body,
                )
            )
        return drafts
