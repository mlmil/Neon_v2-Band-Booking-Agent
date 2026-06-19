import re
from urllib.request import urlopen


CALENDAR_ICS_URL = "https://calendar.google.com/calendar/ical/neonblondevc%40gmail.com/public/basic.ics"


class NeonCalendarContext:
    def describe_date(self, date_text: str) -> str:
        target = _ics_date(date_text)
        if target is None:
            return f"I could not normalize {date_text} for a Calendar check."
        with urlopen(CALENDAR_ICS_URL, timeout=15) as response:
            ics = response.read().decode("utf-8", errors="replace")
        if f"DTSTART;VALUE=DATE:{target}" in ics or re.search(rf"DTSTART[^:]*:{target}T", ics):
            return f"{date_text} is on the Neon calendar."
        return f"{date_text} is not on the Neon calendar."


def _ics_date(value: str) -> str | None:
    months = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
    }
    match = re.search(r"\b(" + "|".join(months) + r")\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?", value, re.I)
    if not match:
        return None
    return f"{match.group(3) or '2026'}{months[match.group(1).lower()]}{int(match.group(2)):02d}"
