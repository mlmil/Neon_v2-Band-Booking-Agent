import re

from telegram_bot.booking_watcher.models import BookingSignal


DATE_PATTERN = re.compile(
    r"\b("
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
    r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b",
    re.IGNORECASE,
)

SIGNAL_RULES = [
    ("cancellation", "high", ("cancel", "canceled", "cancelled", "off", "not happening")),
    ("new_booking", "high", ("booked us", "got us a gig", "confirmed", "they want us")),
    ("reschedule", "high", ("rescheduled", "moved", "new date", "pushed")),
    ("time_change", "high", ("starts at", "load-in changed", "earlier", "later")),
    ("venue_change", "high", ("new address", "different venue", "moved locations")),
    ("hold_or_tentative", "normal", ("hold", "pencil", "tentative", "maybe")),
    ("availability_conflict", "normal", ("i am out", "i'm out", "can't make it", "cannot make it")),
]


def detect_booking_signal(text: str) -> BookingSignal | None:
    normalized = text.lower()
    extracted_date = _extract_date(text)
    for signal_type, priority, keywords in SIGNAL_RULES:
        if any(keyword in normalized for keyword in keywords):
            if signal_type in {"cancellation", "new_booking", "reschedule", "time_change", "venue_change"}:
                priority = "high" if extracted_date else "normal"
            return BookingSignal(
                signal_type=signal_type,
                priority=priority,
                confidence=0.75,
                extracted_date=extracted_date,
                extracted_venue=None,
                reason=f"matched {signal_type} keyword",
            )
    return None


def _extract_date(text: str) -> str | None:
    match = DATE_PATTERN.search(text)
    if match is None:
        return None
    month = match.group(1).strip(".")
    day = match.group(2)
    return f"{month.capitalize()} {int(day)}"
