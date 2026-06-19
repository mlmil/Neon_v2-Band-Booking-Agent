# Telegram Booking Watcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first read-only Telegram Booking Watcher inside `NeonBotstein_Bot` so booking/cancellation chatter becomes durable Calendar Attention Queue items and high-priority band alerts.

**Architecture:** Add focused watcher modules under `Telegram Bot/telegram_bot/booking_watcher/`. The Telegram transport will call an optional incoming-message handler before command replies, allowing group chatter to be archived and flagged while existing slash commands remain stable. Queue state stays local JSONL and Calendar/Band Sheet writes remain forbidden.

**Tech Stack:** Python standard library, existing `unittest` suite, existing Telegram Bot API transport, local JSONL files.

---

## File Structure

- Create `Telegram Bot/telegram_bot/booking_watcher/__init__.py`
  - Exports watcher data types and service.
- Create `Telegram Bot/telegram_bot/booking_watcher/models.py`
  - Defines `ArchivedTelegramMessage`, `BookingSignal`, and `QueueItem`.
- Create `Telegram Bot/telegram_bot/booking_watcher/detector.py`
  - Rules-first detector for cancellation, booking, reschedule, time, venue, hold, and availability signals.
- Create `Telegram Bot/telegram_bot/booking_watcher/store.py`
  - JSONL archive and queue persistence with reviewed/dismissed state updates.
- Create `Telegram Bot/telegram_bot/booking_watcher/service.py`
  - Orchestrates archive, detection, queue creation, and alert text.
- Modify `Telegram Bot/telegram_bot/telegram_transport.py`
  - Add optional incoming-message handler and optional outgoing messages from that handler.
- Modify `Telegram Bot/telegram_bot/responder.py`
  - Add `/flags`, `/flag <id>`, `/reviewed <id>`, `/dismiss <id>`, `/watch-status`.
- Modify `Telegram Bot/telegram_bot/cli.py`
  - Wire watcher service into live polling/run commands and local reply command when store path is available.
- Add tests:
  - `Telegram Bot/tests/test_booking_detector.py`
  - `Telegram Bot/tests/test_booking_store.py`
  - `Telegram Bot/tests/test_booking_service.py`
  - Extend `Telegram Bot/tests/test_telegram_transport.py`
  - Extend `Telegram Bot/tests/test_responder.py`

## Task 1: Booking Signal Detector

**Files:**
- Create: `Telegram Bot/telegram_bot/booking_watcher/__init__.py`
- Create: `Telegram Bot/telegram_bot/booking_watcher/models.py`
- Create: `Telegram Bot/telegram_bot/booking_watcher/detector.py`
- Test: `Telegram Bot/tests/test_booking_detector.py`

- [ ] **Step 1: Write the failing detector tests**

```python
import unittest

from telegram_bot.booking_watcher.detector import detect_booking_signal


class BookingDetectorTests(unittest.TestCase):
    def test_detects_cancellation_with_date_as_high_priority(self) -> None:
        signal = detect_booking_signal("Kyle said the June 27 party is canceled")

        self.assertIsNotNone(signal)
        assert signal is not None
        self.assertEqual(signal.signal_type, "cancellation")
        self.assertEqual(signal.priority, "high")
        self.assertEqual(signal.extracted_date, "June 27")

    def test_detects_confirmed_booking_as_high_priority(self) -> None:
        signal = detect_booking_signal("Alfred booked us at Leashless on July 12")

        self.assertIsNotNone(signal)
        assert signal is not None
        self.assertEqual(signal.signal_type, "new_booking")
        self.assertEqual(signal.priority, "high")
        self.assertEqual(signal.extracted_date, "July 12")

    def test_detects_vague_hold_as_normal_priority(self) -> None:
        signal = detect_booking_signal("Can we hold August 9 for that party?")

        self.assertIsNotNone(signal)
        assert signal is not None
        self.assertEqual(signal.signal_type, "hold_or_tentative")
        self.assertEqual(signal.priority, "normal")
        self.assertEqual(signal.extracted_date, "August 9")

    def test_ordinary_chatter_is_ignored(self) -> None:
        self.assertIsNone(detect_booking_signal("That last set felt great."))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run detector tests and verify RED**

Run: `python3 -m unittest tests.test_booking_detector`

Expected: import failure because `telegram_bot.booking_watcher` does not exist.

- [ ] **Step 3: Implement minimal detector and models**

Create `models.py` with:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class BookingSignal:
    signal_type: str
    priority: str
    confidence: float
    extracted_date: str | None
    extracted_venue: str | None
    reason: str
```

Create `detector.py` with keyword matching and a month/day extractor:

```python
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
            if signal_type in {"cancellation", "new_booking", "reschedule", "time_change", "venue_change"} and extracted_date is None:
                priority = "normal"
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
```

- [ ] **Step 4: Run detector tests and verify GREEN**

Run: `python3 -m unittest tests.test_booking_detector`

Expected: all detector tests pass.

## Task 2: JSONL Archive And Queue Store

**Files:**
- Modify: `Telegram Bot/telegram_bot/booking_watcher/models.py`
- Create: `Telegram Bot/telegram_bot/booking_watcher/store.py`
- Test: `Telegram Bot/tests/test_booking_store.py`

- [ ] **Step 1: Write failing store tests**

```python
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from telegram_bot.booking_watcher.models import ArchivedTelegramMessage, BookingSignal
from telegram_bot.booking_watcher.store import BookingWatcherStore


class BookingWatcherStoreTests(unittest.TestCase):
    def test_archives_message_and_adds_queue_item(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = BookingWatcherStore(Path(temp_dir))
            message = ArchivedTelegramMessage(
                chat_id=-1001,
                message_id=42,
                sender_name="Kyle",
                sender_username="kyle",
                text="June 27 is canceled",
                message_date=1719000000,
            )
            signal = BookingSignal("cancellation", "high", 0.75, "June 27", None, "matched cancellation keyword")

            store.archive_message(message)
            item = store.add_queue_item(message, signal, calendar_match="booked", bandsheet_match="booked")

            self.assertEqual(item.status, "open")
            self.assertEqual(item.signal_type, "cancellation")
            self.assertEqual(len(store.list_open_items()), 1)

    def test_mark_reviewed_updates_queue_status(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = BookingWatcherStore(Path(temp_dir))
            message = ArchivedTelegramMessage(-1001, 42, "Kyle", "kyle", "June 27 is canceled", 1719000000)
            signal = BookingSignal("cancellation", "high", 0.75, "June 27", None, "matched cancellation keyword")
            item = store.add_queue_item(message, signal, calendar_match="booked", bandsheet_match="unknown")

            self.assertTrue(store.mark_reviewed(item.id, reviewed_by="Mike"))

            open_items = store.list_open_items()
            self.assertEqual(open_items, [])
            reviewed = store.get_item(item.id)
            assert reviewed is not None
            self.assertEqual(reviewed.status, "reviewed")
            self.assertEqual(reviewed.reviewed_by, "Mike")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run store tests and verify RED**

Run: `python3 -m unittest tests.test_booking_store`

Expected: import failure for missing store/model classes.

- [ ] **Step 3: Implement store and queue models**

Add `ArchivedTelegramMessage` and `QueueItem` dataclasses to `models.py`. Implement `BookingWatcherStore` with `archive_message()`, `add_queue_item()`, `list_open_items()`, `get_item()`, `mark_reviewed()`, and `mark_dismissed()`. Use append-friendly JSONL for archive and rewrite queue JSONL for state changes.

- [ ] **Step 4: Run store tests and verify GREEN**

Run: `python3 -m unittest tests.test_booking_store`

Expected: all store tests pass.

## Task 3: Watcher Service And Alert Text

**Files:**
- Create: `Telegram Bot/telegram_bot/booking_watcher/service.py`
- Test: `Telegram Bot/tests/test_booking_service.py`

- [ ] **Step 1: Write failing service tests**

```python
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from telegram_bot.booking_watcher.service import BookingWatcherService


class BookingWatcherServiceTests(unittest.TestCase):
    def test_high_priority_message_creates_alert_and_queue_item(self) -> None:
        with TemporaryDirectory() as temp_dir:
            service = BookingWatcherService(Path(temp_dir))

            result = service.handle_text_message(
                chat_id=-1001,
                message_id=42,
                sender_name="Kyle",
                sender_username="kyle",
                text="June 27 is canceled",
                message_date=1719000000,
            )

            self.assertIsNotNone(result.alert_text)
            assert result.alert_text is not None
            self.assertIn("NEON CALENDAR FLAG", result.alert_text)
            self.assertIn("possible cancellation", result.alert_text)
            self.assertEqual(len(service.store.list_open_items()), 1)

    def test_ordinary_message_archives_without_alert(self) -> None:
        with TemporaryDirectory() as temp_dir:
            service = BookingWatcherService(Path(temp_dir))

            result = service.handle_text_message(
                chat_id=-1001,
                message_id=43,
                sender_name="Dave",
                sender_username=None,
                text="Great rehearsal.",
                message_date=1719000001,
            )

            self.assertIsNone(result.alert_text)
            self.assertEqual(service.store.list_open_items(), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run service tests and verify RED**

Run: `python3 -m unittest tests.test_booking_service`

Expected: import failure for missing service.

- [ ] **Step 3: Implement service orchestration**

Implement `BookingWatcherService.handle_text_message()` so it archives every message, detects a signal, creates a queue item for detected signals, and returns alert text only for `priority == "high"`.

- [ ] **Step 4: Run service tests and verify GREEN**

Run: `python3 -m unittest tests.test_booking_service`

Expected: all service tests pass.

## Task 4: Telegram Transport Handler Hook

**Files:**
- Modify: `Telegram Bot/telegram_bot/telegram_transport.py`
- Test: `Telegram Bot/tests/test_telegram_transport.py`

- [ ] **Step 1: Write failing transport test**

Add a test proving group chatter can produce a watcher alert without calling the command reply builder.

- [ ] **Step 2: Run transport test and verify RED**

Run: `python3 -m unittest tests.test_telegram_transport.TelegramTransportTests.test_message_handler_can_send_alert_without_command_reply`

Expected: constructor does not accept the new handler.

- [ ] **Step 3: Implement optional handler**

Add an optional `message_handler` callback to `TelegramBot`. It receives message metadata and returns zero or more outgoing text messages. If the message is a group message and the incoming text is not a command, send handler alerts but skip default command reply.

- [ ] **Step 4: Run transport tests and verify GREEN**

Run: `python3 -m unittest tests.test_telegram_transport`

Expected: all transport tests pass.

## Task 5: `/flags`, `/reviewed`, `/dismiss`, `/watch-status`

**Files:**
- Modify: `Telegram Bot/telegram_bot/responder.py`
- Modify: `Telegram Bot/telegram_bot/cli.py`
- Test: `Telegram Bot/tests/test_responder.py`
- Test: `Telegram Bot/tests/test_cli.py`

- [ ] **Step 1: Write failing responder tests**

Add tests for `/flags` showing open queue items, `/reviewed <id>` marking an item reviewed, `/dismiss <id>` dismissing false positives, and `/watch-status` showing watcher storage status.

- [ ] **Step 2: Run responder tests and verify RED**

Run: `python3 -m unittest tests.test_responder`

Expected: commands return the old fallback message.

- [ ] **Step 3: Implement responder command support**

Allow `build_reply()` to accept an optional watcher store. If no store is passed, watcher commands should say the watcher is not configured. If a store is passed, commands should operate only on local queue state.

- [ ] **Step 4: Run responder tests and verify GREEN**

Run: `python3 -m unittest tests.test_responder`

Expected: all responder tests pass.

## Task 6: CLI Wiring And Live Safety Check

**Files:**
- Modify: `Telegram Bot/telegram_bot/cli.py`
- Test: `Telegram Bot/tests/test_cli.py`
- Modify docs if needed: `Telegram Bot/README.md`

- [ ] **Step 1: Write failing CLI wiring test**

Add a test showing `poll-once` constructs `BookingWatcherService` using a default local data path and passes its store into the responder.

- [ ] **Step 2: Run CLI tests and verify RED**

Run: `python3 -m unittest tests.test_cli`

Expected: watcher service is not constructed.

- [ ] **Step 3: Wire the service**

Use default path `data/telegram/booking_watcher` under the Neon V2 repo. In `poll-once` and `run`, pass a handler that calls `BookingWatcherService.handle_text_message()`. If the service returns alert text, send it to the same group chat.

- [ ] **Step 4: Run full test suite**

Run: `python3 -m unittest discover -s tests`

Expected: all tests pass.

- [ ] **Step 5: Health check live bot identity**

Run: `python3 -m telegram_bot health`

Expected: `ok: NeonBotstein_Bot`

## Self-Review Notes

- Spec coverage: archive, detect, queue, band-wide high-priority alerts, commands, local-only state, and Mike-write-only Calendar authority are covered.
- Intentional V1 gap: read-only Calendar/Band Sheet cross-check starts as `unknown/booked` plumbing unless existing providers make exact matching cheap during implementation. The queue schema supports real cross-checking in the next slice.
- No Calendar, Band Sheet, email, WordPress, or payment writes are included.
