import argparse
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from telegram_bot.booking_watcher.service import BookingWatcherService
from telegram_bot.gemini_agent import GeminiNeonAgent as GeminiQuestionAnswerer
from telegram_bot.models import BandSheetSnapshot
from telegram_bot.providers.bandsheet import BandSheetProviderError, BandSheetSnapshotProvider
from telegram_bot.providers.closeout import CloseoutQueueProvider
from telegram_bot.providers.payout import PayoutCaptureProvider
from telegram_bot.providers.pending_drafts import PendingDraftsProvider
from telegram_bot.providers.rehearsals import FreshgroundRehearsalProvider
from telegram_bot.responder import build_reply
from telegram_bot.telegram_transport import IncomingTelegramMessage, TelegramBot, TelegramConfig, TelegramTransportError

DEFAULT_TOKEN_PATH = Path.home() / ".hermes" / "secure" / "neon_bot_token.txt"
DEFAULT_STATE_PATH = Path.home() / ".hermes" / "neon_bot_state.json"
DEFAULT_WATCHER_ROOT = Path(__file__).resolve().parents[2] / "data" / "telegram" / "booking_watcher"
EXPECTED_TELEGRAM_USERNAME = "NeonBotstein_Bot"
MIKE_TELEGRAM_CHAT_ID = 7118814432


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Neon Telegram bot utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("bandsheet-snapshot", help="Print the normalized BandSheet snapshot.")
    snapshot.add_argument(
        "--fixture",
        type=Path,
        help="Load BandSheet JSON from a local fixture instead of the live public endpoint.",
    )
    snapshot.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Exit non-zero when the BandSheet source is stale.",
    )

    reply = subparsers.add_parser("reply", help="Render a read-only reply for a Telegram-style message.")
    reply.add_argument("message", help="Incoming message text.")
    reply.add_argument(
        "--fixture",
        type=Path,
        help="Load BandSheet JSON from a local fixture instead of the live public endpoint.",
    )
    reply.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Exit non-zero when the BandSheet source is stale.",
    )
    reply.add_argument("--no-gemini", action="store_true", help="Disable Gemini fallback answers.")

    poll_once = subparsers.add_parser("poll-once", help="Process one Telegram long-poll cycle.")
    poll_once.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_PATH)
    poll_once.add_argument("--env-file", type=Path)
    poll_once.add_argument("--state-file", type=Path, default=DEFAULT_STATE_PATH)
    poll_once.add_argument(
        "--fixture",
        type=Path,
        help="Load BandSheet JSON from a local fixture instead of the live public endpoint.",
    )
    poll_once.add_argument("--no-gemini", action="store_true", help="Disable Gemini fallback answers.")

    run = subparsers.add_parser("run", help="Run the Telegram long-poll loop.")
    run.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_PATH)
    run.add_argument("--env-file", type=Path)
    run.add_argument("--state-file", type=Path, default=DEFAULT_STATE_PATH)
    run.add_argument("--max-cycles", type=int)
    run.add_argument("--sleep-seconds", type=float, default=5.0)
    run.add_argument(
        "--fixture",
        type=Path,
        help="Load BandSheet JSON from a local fixture instead of the live public endpoint.",
    )
    run.add_argument("--no-gemini", action="store_true", help="Disable Gemini fallback answers.")

    health = subparsers.add_parser("health", help="Check Telegram bot identity without polling updates.")
    health.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_PATH)
    health.add_argument("--env-file", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "bandsheet-snapshot":
        return _print_bandsheet_snapshot(args.fixture, fail_on_stale=args.fail_on_stale)
    if args.command == "reply":
        return _print_reply(args.message, args.fixture, fail_on_stale=args.fail_on_stale, use_gemini=not args.no_gemini)
    if args.command == "poll-once":
        return _poll_once(args.token_file, args.state_file, fixture=args.fixture, env_file=args.env_file, use_gemini=not args.no_gemini)
    if args.command == "run":
        return _run(
            args.token_file,
            args.state_file,
            fixture=args.fixture,
            env_file=args.env_file,
            use_gemini=not args.no_gemini,
            max_cycles=args.max_cycles,
            sleep_seconds=args.sleep_seconds,
        )
    if args.command == "health":
        return _health(args.token_file, env_file=args.env_file)
    raise AssertionError(f"Unhandled command: {args.command}")


def _print_bandsheet_snapshot(fixture: Path | None, *, fail_on_stale: bool) -> int:
    try:
        snapshot = _load_snapshot(fixture, fail_on_stale=fail_on_stale)
    except BandSheetProviderError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        return 1

    print(json.dumps({"status": "success", "snapshot": _to_jsonable(snapshot)}, indent=2))
    return 0


def _print_reply(message: str, fixture: Path | None, *, fail_on_stale: bool, use_gemini: bool) -> int:
    try:
        snapshot = _load_snapshot(fixture, fail_on_stale=fail_on_stale)
    except BandSheetProviderError as exc:
        print(f"BandSheet unavailable: {exc}")
        return 1

    watcher = BookingWatcherService(DEFAULT_WATCHER_ROOT)
    question_answerer = GeminiQuestionAnswerer(allow_send=False) if use_gemini else None
    pending_drafts = PendingDraftsProvider().list_drafts()
    print(_build_reply(message, snapshot, watcher=watcher, question_answerer=question_answerer, pending_drafts=pending_drafts))
    return 0


def _load_snapshot(fixture: Path | None, *, fail_on_stale: bool) -> BandSheetSnapshot:
    provider = BandSheetSnapshotProvider(
        fail_on_stale=fail_on_stale,
        fetcher=_fixture_fetcher(fixture) if fixture else None,
    )
    return provider.load_snapshot()


def _poll_once(
    token_file: Path,
    state_file: Path,
    *,
    fixture: Path | None,
    env_file: Path | None = None,
    use_gemini: bool = True,
) -> int:
    bot = _build_bot(token_file, state_file, fixture=fixture, env_file=env_file, use_gemini=use_gemini)
    try:
        processed = bot.process_once()
    except TelegramTransportError as exc:
        print(f"Telegram unavailable: {exc}")
        return 1
    print(f"processed {processed} update(s)")
    return 0


def _run(
    token_file: Path,
    state_file: Path,
    *,
    fixture: Path | None,
    env_file: Path | None = None,
    use_gemini: bool,
    max_cycles: int | None,
    sleep_seconds: float,
) -> int:
    bot = _build_bot(token_file, state_file, fixture=fixture, env_file=env_file, use_gemini=use_gemini)
    try:
        processed = bot.run(max_cycles=max_cycles, sleep_seconds=sleep_seconds)
    except TelegramTransportError as exc:
        print(f"Telegram unavailable: {exc}")
        return 1
    print(f"processed {processed} update(s)")
    return 0


def _health(token_file: Path, *, env_file: Path | None = None) -> int:
    config = _load_telegram_config(token_file, env_file=env_file)
    bot = TelegramBot(config=config, state_path=DEFAULT_STATE_PATH, reply_builder=lambda text: text)
    try:
        identity = bot.get_me()
    except TelegramTransportError as exc:
        print(f"Telegram unavailable: {exc}")
        return 1

    username = identity.get("username")
    if username != EXPECTED_TELEGRAM_USERNAME:
        print(f"wrong bot: {username}")
        return 1
    print(f"ok: {username}")
    return 0


def _load_telegram_config(token_file: Path, *, env_file: Path | None) -> TelegramConfig:
    return TelegramConfig.from_env_file(env_file) if env_file else TelegramConfig.from_token_file(token_file)


def _build_bot(
    token_file: Path,
    state_file: Path,
    *,
    fixture: Path | None,
    env_file: Path | None,
    use_gemini: bool,
) -> TelegramBot:
    config = _load_telegram_config(token_file, env_file=env_file)
    watcher = BookingWatcherService(DEFAULT_WATCHER_ROOT)
    question_answerer = GeminiQuestionAnswerer(allow_send=True) if use_gemini else None
    payout_capture = PayoutCaptureProvider()
    pending_drafts_provider = PendingDraftsProvider()

    def reply_builder(message: str) -> str:
        snapshot = _load_snapshot(fixture, fail_on_stale=False)
        return _build_reply(
            message,
            snapshot,
            watcher=watcher,
            question_answerer=question_answerer,
            payout_capture=payout_capture,
            pending_drafts=pending_drafts_provider.list_drafts(),
        )

    return TelegramBot(
        config=config,
        state_path=state_file,
        reply_builder=reply_builder,
        message_handler=watcher.handle_incoming_message,
        cycle_handler=lambda: _due_reminders(question_answerer),
    )


def _build_reply(
    message: str,
    snapshot: BandSheetSnapshot,
    *,
    watcher: BookingWatcherService | None = None,
    question_answerer=None,
    payout_capture=None,
    pending_drafts=None,
) -> str:
    normalized = message.strip().lower()
    rehearsals = _safe_rehearsals() if normalized in {"/rehearsals", "rehearsals"} else None
    closeouts = _safe_closeouts() if normalized in {"/closeout", "closeout"} else None
    return build_reply(
        message,
        snapshot,
        rehearsals=rehearsals,
        closeouts=closeouts,
        watcher_store=watcher.store if watcher else None,
        payout_capture=payout_capture,
        question_answerer=question_answerer,
        pending_drafts=pending_drafts,
    )


def _safe_rehearsals() -> list[str]:
    try:
        return FreshgroundRehearsalProvider().upcoming()
    except Exception:
        return []


def _safe_closeouts() -> list[str]:
    try:
        return CloseoutQueueProvider().needs_closeout()
    except Exception:
        return []


def _due_reminders(question_answerer) -> list[tuple[int, str]]:
    if question_answerer is None or not hasattr(question_answerer, "due_reminder"):
        return []
    reminder = question_answerer.due_reminder()
    return [(MIKE_TELEGRAM_CHAT_ID, reminder)] if reminder else []


def _fixture_fetcher(fixture: Path):
    def fetch(_: str) -> object:
        with fixture.open(encoding="utf-8") as handle:
            return json.load(handle)

    return fetch


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return {key: _to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


if __name__ == "__main__":
    raise SystemExit(main())
