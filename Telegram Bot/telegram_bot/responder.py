from telegram_bot.models import BandSheetBookedGig, BandSheetSnapshot
from telegram_bot.booking_watcher.store import BookingWatcherStore
from telegram_bot.providers.pending_drafts import PendingDraft


def build_reply(
    message_text: str,
    snapshot: BandSheetSnapshot,
    *,
    rehearsals: list[str] | None = None,
    closeouts: list[str] | None = None,
    watcher_store: BookingWatcherStore | None = None,
    payout_capture=None,
    question_answerer=None,
    pending_drafts: list[PendingDraft] | None = None,
) -> str:
    normalized = message_text.strip().lower()
    if payout_capture is not None:
        payout_reply = payout_capture.maybe_record(message_text)
        if payout_reply is not None:
            return payout_reply
    if normalized in {"/help", "help", "?"}:
        return _help_reply()
    if _is_draft_list_request(normalized):
        return _draft_list_reply(pending_drafts or [])
    if _is_draft_detail_request(normalized):
        return _draft_detail_reply(_matching_draft(message_text, pending_drafts or []), len(pending_drafts or []))
    if normalized in {"/flags", "flags"}:
        return _flags_reply(watcher_store)
    if normalized == "/flag" or normalized == "flag":
        return "Send /flag <id> to show one Calendar Attention Queue item."
    if normalized.startswith("/flag ") or normalized.startswith("flag "):
        item_id = message_text.strip().split(maxsplit=1)[1].strip()
        return _flag_detail_reply(watcher_store, item_id)
    if normalized == "/reviewed" or normalized == "reviewed":
        return "Send /reviewed <id> after Mike handles the calendar item manually."
    if normalized.startswith("/reviewed ") or normalized.startswith("reviewed "):
        item_id = message_text.strip().split(maxsplit=1)[1].strip()
        return _mark_reply(watcher_store, item_id, action="reviewed")
    if normalized == "/dismiss" or normalized == "dismiss":
        return "Send /dismiss <id> to close a false positive."
    if normalized.startswith("/dismiss ") or normalized.startswith("dismiss "):
        item_id = message_text.strip().split(maxsplit=1)[1].strip()
        return _mark_reply(watcher_store, item_id, action="dismiss")
    if normalized in {"/watch-status", "watch-status"}:
        return _watch_status_reply(watcher_store)
    if normalized in {"/gigs", "gigs", "upcoming", "upcoming gigs"}:
        return _gigs_reply(snapshot)
    if normalized in {"/status", "status", "bandsheet status"}:
        return _status_reply(snapshot)
    if normalized in {"/members-out", "members-out", "members out"}:
        return _list_reply("Member availability notes:", snapshot.members_out, empty="No member availability notes found.")
    if normalized in {"/this-week", "this-week", "this week"}:
        return _list_reply("This week:", snapshot.this_week, empty="No this-week notes found.")
    if normalized in {"/free", "free", "open dates", "open days"}:
        return _free_reply(snapshot)
    if normalized == "/venue" or normalized == "venue":
        return "Send /venue <name> to search upcoming Band Sheet gigs by venue."
    if normalized.startswith("/venue ") or normalized.startswith("venue "):
        query = message_text.strip().split(maxsplit=1)[1].strip()
        return _venue_reply(query, snapshot)
    if normalized in {"/rehearsals", "rehearsals"}:
        return _list_reply("Freshground rehearsals:", rehearsals or [], empty="No upcoming Freshground Neon rehearsals found.")
    if normalized in {"/closeout", "closeout"}:
        return _closeout_reply(closeouts or [])
    if question_answerer is not None:
        return _question_answerer_reply(question_answerer, message_text.strip(), snapshot)
    return "I can only answer read-only BandSheet questions right now. Send /help."


def _help_reply() -> str:
    return "\n".join(
        [
            "Neon Telegram bot",
            "/gigs - list upcoming BandSheet gigs",
            "/status - show BandSheet freshness",
            "/members-out - show member availability notes",
            "/this-week - show this week's Band Sheet notes",
            "/free - show Band Sheet open dates with freshness context",
            "/venue <name> - find upcoming gigs by venue",
            "/rehearsals - rehearsal source status",
            "/closeout - post-gig closeout source status",
            "/drafts - list pending AgentMail drafts",
            "/draft - show the pending AgentMail draft",
            "tip jar 200, venmo 100, payout 500 - write post-gig payout numbers",
            "/flags - show calendar attention items from Telegram",
            "/reviewed <id> - mark an item reviewed after Mike handles it",
            "/watch-status - show Telegram booking watcher status",
            "/help - show this list",
            "",
            "Examples:",
            "Try: gigs",
            "Try: status",
            "Try: venue leashless",
            "Try: members out",
            "Try: this week",
        ]
    )


def _gigs_reply(snapshot: BandSheetSnapshot) -> str:
    lines = ["Upcoming gigs:"]
    for gig in snapshot.booked_gigs:
        lines.append(_format_gig(gig))
    if snapshot.source.is_stale:
        lines.append("")
        lines.append("BandSheet source is stale. Treat this as a draft view until manual verification.")
    return "\n".join(lines)


def _status_reply(snapshot: BandSheetSnapshot) -> str:
    updated = snapshot.source.updated_at.date().isoformat()
    if snapshot.source.is_stale:
        return (
            f"BandSheet source is stale: updated {updated}, "
            f"{snapshot.source.freshness_days} days old. Use manual verification before routing."
        )
    return f"BandSheet source is fresh: updated {updated}, {snapshot.source.freshness_days} days old."


def _free_reply(snapshot: BandSheetSnapshot) -> str:
    lines = _list_lines("Band Sheet open dates:", snapshot.free_weekends, empty="No Band Sheet open dates found.")
    updated = snapshot.source.updated_at.date().isoformat()
    if snapshot.source.is_stale:
        lines.extend(
            [
                "",
                f"Freshness: stale, updated {updated}. Use manual verification before treating these as available.",
            ]
        )
    else:
        lines.extend(["", f"Freshness: updated {updated}."])
    return "\n".join(lines)


def _venue_reply(query: str, snapshot: BandSheetSnapshot) -> str:
    normalized_query = query.lower()
    matches = [
        gig
        for gig in snapshot.booked_gigs
        if normalized_query in gig.summary.lower()
        or (gig.venue_name is not None and normalized_query in gig.venue_name.lower())
        or (gig.city is not None and normalized_query in gig.city.lower())
    ]
    if not matches:
        return f"No upcoming Band Sheet gigs found for {query}."

    lines = [f"Matching gigs for {query}:"]
    lines.extend(_format_gig(gig) for gig in matches)
    if snapshot.source.is_stale:
        lines.append("")
        lines.append("BandSheet source is stale. Confirm before using this for routing.")
    return "\n".join(lines)


def _closeout_reply(closeouts: list[str]) -> str:
    lines = _list_lines("Post-gig closeout queue:", closeouts, empty="No post-gig closeout items found.")
    lines.append("")
    lines.append("read-only summary. Use the payout/closeout tools before marking anything closed.")
    return "\n".join(lines)


def _draft_list_reply(drafts: list[PendingDraft]) -> str:
    if not drafts:
        return "No pending AgentMail drafts found."
    noun = "draft" if len(drafts) == 1 else "drafts"
    lines = [f"{len(drafts)} AgentMail {noun} awaiting review:"]
    for index, draft in enumerate(drafts, 1):
        recipients = ", ".join(draft.to) or "recipient unclear"
        lines.append(f"- {index}. {draft.subject} -> {recipients}")
    lines.extend(["", 'Say "show me the draft" to read it. Nothing has been sent.'])
    return "\n".join(lines)


def _draft_detail_reply(draft: PendingDraft | None, total: int) -> str:
    if draft is None:
        return "No matching pending AgentMail draft found."
    recipients = ", ".join(draft.to) or "recipient unclear"
    position = "1 of 1" if total == 1 else f"matching {total} pending"
    return "\n".join(
        [
            f"Pending AgentMail draft {position}",
            f"Contact: {draft.from_name or 'unknown'}",
            f"To: {recipients}",
            f"Subject: {draft.subject}",
            "",
            draft.body.strip(),
            "",
            "Status: draft only, not sent.",
        ]
    )


def _is_draft_list_request(normalized: str) -> bool:
    return normalized in {"/drafts", "/agentmail"}


def _is_draft_detail_request(normalized: str) -> bool:
    return normalized == "/draft"


def _matching_draft(message_text: str, drafts: list[PendingDraft]) -> PendingDraft | None:
    if not drafts:
        return None
    normalized = message_text.lower()
    if "philip" in normalized or "phillip" in normalized:
        for draft in drafts:
            if "phillip" in draft.from_name.lower() or any("rockstarentertainment805" in value.lower() for value in draft.to):
                return draft
    return drafts[0]


def _flags_reply(watcher_store: BookingWatcherStore | None) -> str:
    if watcher_store is None:
        return _watcher_unconfigured_reply()
    items = watcher_store.list_open_items()
    if not items:
        return "Calendar attention queue:\nNo open Telegram booking flags."
    lines = ["Calendar attention queue:"]
    for item in items:
        date = item.extracted_date or "date unclear"
        lines.append(f"- {item.id}: {item.signal_type} from {item.source_sender_name} ({date})")
    return "\n".join(lines)


def _flag_detail_reply(watcher_store: BookingWatcherStore | None, item_id: str) -> str:
    if watcher_store is None:
        return _watcher_unconfigured_reply()
    item = watcher_store.get_item(item_id)
    if item is None:
        return f"No Calendar Attention Queue item found for {item_id}."
    return "\n".join(
        [
            f"Calendar flag {item.id}",
            f"Status: {item.status}",
            f"Type: {item.signal_type}",
            f"Source: {item.source_sender_name}",
            f"Date: {item.extracted_date or 'unclear'}",
            f"Calendar: {item.calendar_match}",
            f"Band Sheet: {item.bandsheet_match}",
            f'Message: "{item.message_text}"',
        ]
    )


def _mark_reply(watcher_store: BookingWatcherStore | None, item_id: str, *, action: str) -> str:
    if watcher_store is None:
        return _watcher_unconfigured_reply()
    if action == "reviewed":
        changed = watcher_store.mark_reviewed(item_id, reviewed_by="Mike")
        verb = "Marked reviewed"
    else:
        changed = watcher_store.mark_dismissed(item_id, reviewed_by="Mike")
        verb = "Dismissed"
    if not changed:
        return f"No Calendar Attention Queue item found for {item_id}."
    return f"{verb}: {item_id}.\nNo Calendar changes were made."


def _watch_status_reply(watcher_store: BookingWatcherStore | None) -> str:
    if watcher_store is None:
        return _watcher_unconfigured_reply()
    return "\n".join(
        [
            "Telegram booking watcher: configured",
            f"Queue path: {watcher_store.queue_path}",
            f"Open flags: {len(watcher_store.list_open_items())}",
        ]
    )


def _watcher_unconfigured_reply() -> str:
    return "Telegram booking watcher is not configured for this command context."


def _question_answerer_reply(question_answerer, question: str, snapshot: BandSheetSnapshot) -> str:
    try:
        reply = question_answerer(question, snapshot)
    except Exception:
        return "I couldn't verify that through the read-only answer engine. Send /help for fixed commands."
    if not isinstance(reply, str) or not reply.strip():
        return "I couldn't verify that through the read-only answer engine. Send /help for fixed commands."
    return reply.strip()


def _list_reply(title: str, items: list[str], *, empty: str) -> str:
    return "\n".join(_list_lines(title, items, empty=empty))


def _list_lines(title: str, items: list[str], *, empty: str) -> list[str]:
    if not items:
        return [title, empty]
    return [title, *items]


def _format_gig(gig: BandSheetBookedGig) -> str:
    if not gig.date or not gig.start_time or not gig.venue_name:
        return gig.summary

    base = f"{gig.date} @ {gig.start_time} - {gig.venue_name}"
    if gig.city:
        return f"{base} ({gig.city})"
    return base
