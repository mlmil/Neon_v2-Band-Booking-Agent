from gig_copilot_bot.models import MemberProfile
from gig_copilot_bot.profile_store import ProfileStore
from gig_copilot_bot.gemini_provider import GeminiProviderError


def build_reply(message_text: str, store: ProfileStore, *, gemini: object | None = None) -> str:
    normalized = message_text.strip().lower()
    if normalized in {"/start", "start"}:
        return _start_reply()
    if normalized in {"/help", "help"}:
        return _help_reply()
    if normalized in {"/onboard", "onboard"}:
        store.save_profile(_default_mike_profile())
        return "Mike onboarding saved. Use /profile to review it."
    if normalized in {"/profile", "profile"}:
        return _profile_reply(store)
    if normalized in {"/simulate-show-day", "simulate-show-day"}:
        return _simulation_reply()
    if normalized in {"/status", "status"}:
        return _status_reply(store)
    if gemini is not None:
        try:
            return gemini.generate(_gemini_prompt(message_text, store))
        except GeminiProviderError:
            return "Gemini unavailable right now. I can still handle /onboard, /profile, /simulate-show-day, and /status."
    return "I only handle Mike-only Gig Copilot test commands right now. Send /help."


def _start_reply() -> str:
    return "\n".join(
        [
            "GigCopilotNeon_Bot is online.",
            "Mode: Mike-only test mode.",
            "Start with /onboard, then /simulate-show-day.",
        ]
    )


def _help_reply() -> str:
    return "\n".join(
        [
            "Gig Copilot commands:",
            "/onboard - save Mike's default logistics profile",
            "/profile - show Mike's saved profile",
            "/simulate-show-day - preview the day-of-show flow to Mike only",
            "/status - show bot mode and profile status",
            "/help - show this list",
        ]
    )


def _profile_reply(store: ProfileStore) -> str:
    profile = store.load_profile("mike")
    if profile is None:
        return "No Mike profile saved yet. Send /onboard."

    alternates = ", ".join(profile.alternate_origin_cities) if profile.alternate_origin_cities else "none"
    live_location = "yes" if profile.live_location_required else "no"
    return "\n".join(
        [
            f"Profile: {profile.name}",
            f"Role: {profile.role}",
            f"Default origin: {profile.default_origin_city}",
            f"Alternate origins: {alternates}",
            f"Standard arrival: {profile.standard_arrival_minutes} minutes before start",
            f"PA/load-in arrival: {profile.pa_load_in_arrival_minutes} minutes before start",
            f"Live location required: {live_location}",
        ]
    )


def _simulation_reply() -> str:
    return "\n".join(
        [
            "SIMULATION - Mike only",
            "",
            "Band-wide kickoff preview:",
            "Day-of-show check-in for Neon Blonde. I found a Band Sheet gig and will coordinate logistics.",
            "",
            "Mike personal route prompt:",
            "Assuming you're leaving from Ventura. For PA/load-in, target arrival is 2 hours before start.",
            "",
            "Example member route prompt:",
            "Kyle, assuming Calabasas, reply with another city if that is wrong.",
            "",
            "Example late-risk alert:",
            "Route alert: Kyle is at risk for arriving late by 10+ minutes.",
            "",
            "No band messages sent. No member messages sent.",
        ]
    )


def _status_reply(store: ProfileStore) -> str:
    profile_state = "saved" if store.load_profile("mike") else "missing"
    return "\n".join(
        [
            "GigCopilotNeon_Bot status",
            "mode: Mike-only test",
            f"Mike profile: {profile_state}",
        ]
    )


def _gemini_prompt(message_text: str, store: ProfileStore) -> str:
    profile = store.load_profile("mike")
    profile_context = "No Mike profile saved yet."
    if profile is not None:
        alternates = ", ".join(profile.alternate_origin_cities) if profile.alternate_origin_cities else "none"
        profile_context = (
            f"Mike profile: role={profile.role}; default_origin={profile.default_origin_city}; "
            f"alternate_origins={alternates}; standard_arrival={profile.standard_arrival_minutes} minutes; "
            f"pa_load_in_arrival={profile.pa_load_in_arrival_minutes} minutes; "
            f"live_location_required={profile.live_location_required}."
        )
    return "\n".join(
        [
            "You are powering GigCopilotNeon_Bot for Neon Blonde.",
            "Mode: Mike-only test mode.",
            "Do not claim that any message was sent to the band.",
            "Do not say you updated calendars, Band Sheet, email, WordPress, payments, or member data.",
            "Keep the answer short, practical, and logistics-focused.",
            profile_context,
            f"Mike message: {message_text}",
        ]
    )


def _default_mike_profile() -> MemberProfile:
    return MemberProfile(
        member_id="mike",
        name="Mike",
        role="Bass + PA setup",
        default_origin_city="Ventura",
        alternate_origin_cities=["Oxnard", "Santa Barbara"],
        standard_arrival_minutes=60,
        pa_load_in_arrival_minutes=120,
        live_location_required=True,
    )
