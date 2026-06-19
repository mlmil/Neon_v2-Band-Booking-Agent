import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

from gig_copilot_bot.gemini_provider import GeminiProvider, load_gemini_api_key
from gig_copilot_bot.gig_day_broadcast import GigDayBroadcaster
from gig_copilot_bot.profile_store import ProfileStore
from gig_copilot_bot.responder import build_reply
from gig_copilot_bot.telegram_transport import TelegramBot, TelegramConfig, TelegramTransportError

EXPECTED_TELEGRAM_USERNAME = "GigCopilotNeon_Bot"
DEFAULT_TOKEN_PATH = Path.home() / ".hermes" / "secure" / "gig_copilot_neon_bot_token.txt"
DEFAULT_STATE_PATH = Path.home() / ".hermes" / "gig_copilot_neon_state.json"
DEFAULT_PROFILES_PATH = Path.home() / ".hermes" / "gig_copilot_neon_profiles.json"
DEFAULT_RECEIPT_PATH = Path.home() / ".hermes" / "gig_copilot_neon_group_receipts.json"
DEFAULT_GROUP_CHAT_ID = -1004424634571
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mike-only Gig Copilot Neon bot utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    reply = subparsers.add_parser("reply", help="Render a local reply without Telegram transport.")
    reply.add_argument("message")
    reply.add_argument("--profiles-file", type=Path, default=DEFAULT_PROFILES_PATH)

    health = subparsers.add_parser("health", help="Check Telegram bot identity.")
    health.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_PATH)

    poll_once = subparsers.add_parser("poll-once", help="Process one Telegram long-poll cycle.")
    poll_once.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_PATH)
    poll_once.add_argument("--state-file", type=Path, default=DEFAULT_STATE_PATH)
    poll_once.add_argument("--profiles-file", type=Path, default=DEFAULT_PROFILES_PATH)

    run = subparsers.add_parser("run", help="Run the Telegram long-poll loop.")
    run.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_PATH)
    run.add_argument("--state-file", type=Path, default=DEFAULT_STATE_PATH)
    run.add_argument("--profiles-file", type=Path, default=DEFAULT_PROFILES_PATH)
    run.add_argument("--max-cycles", type=int)
    run.add_argument("--sleep-seconds", type=float, default=5.0)
    run.add_argument("--enable-gig-day-updates", action="store_true")
    run.add_argument("--group-chat-id", type=int, default=DEFAULT_GROUP_CHAT_ID)
    run.add_argument("--receipt-file", type=Path, default=DEFAULT_RECEIPT_PATH)

    gig_day = subparsers.add_parser("gig-day-update", help="Send or preview today's band-group gig update.")
    gig_day.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_PATH)
    gig_day.add_argument("--group-chat-id", type=int, default=DEFAULT_GROUP_CHAT_ID)
    gig_day.add_argument("--receipt-file", type=Path, default=DEFAULT_RECEIPT_PATH)
    gig_day.add_argument("--date", dest="target_date")
    gig_day.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "reply":
        print(build_reply(args.message, ProfileStore(args.profiles_file), gemini=_load_gemini()))
        return 0
    if args.command == "health":
        return _health(args.token_file)
    if args.command == "poll-once":
        return _poll_once(args.token_file, args.state_file, args.profiles_file)
    if args.command == "run":
        return _run(
            args.token_file,
            args.state_file,
            args.profiles_file,
            max_cycles=args.max_cycles,
            sleep_seconds=args.sleep_seconds,
            enable_gig_day_updates=args.enable_gig_day_updates,
            group_chat_id=args.group_chat_id,
            receipt_file=args.receipt_file,
        )
    if args.command == "gig-day-update":
        target_date = date.fromisoformat(args.target_date) if args.target_date else date.today()
        return _gig_day_update(
            args.token_file,
            group_chat_id=args.group_chat_id,
            receipt_file=args.receipt_file,
            target_date=target_date,
            dry_run=args.dry_run,
        )
    raise AssertionError(f"Unhandled command: {args.command}")


def _health(token_file: Path) -> int:
    bot = TelegramBot(
        config=TelegramConfig.from_token_file(token_file),
        state_path=DEFAULT_STATE_PATH,
        reply_builder=lambda text: text,
    )
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


def _poll_once(token_file: Path, state_file: Path, profiles_file: Path) -> int:
    bot = _build_bot(token_file, state_file, profiles_file)
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
    profiles_file: Path,
    *,
    max_cycles: int | None,
    sleep_seconds: float,
    enable_gig_day_updates: bool = False,
    group_chat_id: int = DEFAULT_GROUP_CHAT_ID,
    receipt_file: Path = DEFAULT_RECEIPT_PATH,
) -> int:
    bot = _build_bot(token_file, state_file, profiles_file)
    try:
        if enable_gig_day_updates:
            processed = _run_with_gig_day_updates(
                bot,
                max_cycles=max_cycles,
                sleep_seconds=sleep_seconds,
                group_chat_id=group_chat_id,
                receipt_file=receipt_file,
            )
        else:
            processed = bot.run(max_cycles=max_cycles, sleep_seconds=sleep_seconds)
    except TelegramTransportError as exc:
        print(f"Telegram unavailable: {exc}")
        return 1
    print(f"processed {processed} update(s)")
    return 0


def _run_with_gig_day_updates(
    bot: TelegramBot,
    *,
    max_cycles: int | None,
    sleep_seconds: float,
    group_chat_id: int,
    receipt_file: Path,
) -> int:
    processed_total = 0
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        processed_total += bot.process_once()
        try:
            _send_gig_day_updates(bot, group_chat_id=group_chat_id, receipt_file=receipt_file, target_date=date.today())
        except Exception as exc:
            print(f"Gig-day update skipped: {exc}")
        cycles += 1
        if max_cycles is None or cycles < max_cycles:
            time.sleep(sleep_seconds)
    return processed_total


def _gig_day_update(
    token_file: Path,
    *,
    group_chat_id: int,
    receipt_file: Path,
    target_date: date,
    dry_run: bool,
) -> int:
    if dry_run:
        bot = _DryRunBot()
    else:
        bot = TelegramBot(
            config=TelegramConfig.from_token_file(token_file),
            state_path=DEFAULT_STATE_PATH,
            reply_builder=lambda text: text,
        )
    result = _send_gig_day_updates(
        bot,
        group_chat_id=group_chat_id,
        receipt_file=receipt_file,
        target_date=target_date,
        dry_run=dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


def _send_gig_day_updates(
    bot: TelegramBot,
    *,
    group_chat_id: int,
    receipt_file: Path,
    target_date: date,
    dry_run: bool = False,
) -> dict[str, object]:
    broadcaster = GigDayBroadcaster(
        group_chat_id=group_chat_id,
        receipt_path=receipt_file,
        send_message=bot.send_message,
    )
    return broadcaster.send_for_gigs(_load_live_calendar_gigs(), target_date=target_date, dry_run=dry_run)


def _load_live_calendar_gigs() -> list[dict[str, str]]:
    from scripts.bandsheet_verification_report import PUBLIC_CALENDAR_ICS_URL, fetch_text, parse_calendar_ics

    return parse_calendar_ics(fetch_text(PUBLIC_CALENDAR_ICS_URL))


class _DryRunBot:
    def send_message(self, chat_id: int, text: str) -> None:
        raise RuntimeError("dry-run must not send Telegram messages")


def _build_bot(token_file: Path, state_file: Path, profiles_file: Path) -> TelegramBot:
    store = ProfileStore(profiles_file)
    gemini = _load_gemini()
    return TelegramBot(
        config=TelegramConfig.from_token_file(token_file),
        state_path=state_file,
        reply_builder=lambda text: build_reply(text, store, gemini=gemini),
    )


def _load_gemini() -> GeminiProvider | None:
    api_key = load_gemini_api_key()
    return GeminiProvider(api_key=api_key) if api_key else None


if __name__ == "__main__":
    raise SystemExit(main())
