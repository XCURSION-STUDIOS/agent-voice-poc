"""Create and inspect Content Calendar events without starting the voice bot.

Examples:
    uv run python -m scripts.test_calendar_agent
    uv run python -m scripts.test_calendar_agent --title "Record video" \
        --start "2026-09-21T14:00:00+08:00" \
        --end "2026-09-21T15:00:00+08:00"
    uv run python -m scripts.test_calendar_agent --title "Draft post" \
        --start "2026-09-21T14:00:00+08:00" \
        --end "2026-09-21T15:00:00+08:00" --yes
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from app.agents.calendar_agent import CalendarAgent
from app.config.settings import get_settings
from app.integrations.notion_calendar import NotionCalendarStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test the Notion-backed calendar agent")
    parser.add_argument("--title", help="Event title")
    parser.add_argument("--start", help="ISO-8601 start, including timezone")
    parser.add_argument("--end", help="ISO-8601 end, including timezone")
    parser.add_argument("--notes", help="Optional notes to add to the Notion page")
    parser.add_argument(
        "--yes", action="store_true", help="Create without the interactive confirmation prompt"
    )
    return parser.parse_args()


def required_value(value: str | None, prompt: str) -> str:
    return value or input(f"{prompt}: ").strip()


async def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    settings = get_settings()
    if not settings.notion_api_key or not settings.notion_database_id:
        raise SystemExit("Set NOTION_API_KEY and NOTION_DATABASE_ID in backend/.env first.")

    args = parse_args()
    title = required_value(args.title, "Event title")
    start = datetime.fromisoformat(required_value(args.start, "Start (ISO-8601)"))
    end = datetime.fromisoformat(required_value(args.end, "End (ISO-8601)"))
    if end <= start:
        raise SystemExit("End must be after start.")

    store = NotionCalendarStore(
        settings.notion_api_key.get_secret_value(), settings.notion_database_id
    )
    agent = CalendarAgent(store)
    proposal = await agent.propose_event(title, start, end, args.notes)

    print("\nCalendar proposal")
    print(f"  Title: {title}")
    print(f"  Start: {start.isoformat()}")
    print(f"  End:   {end.isoformat()}")
    if proposal["conflicts"]:
        print("\nConflicts found:")
        for conflict in proposal["conflicts"]:
            print(
                f"  - {conflict['title']}: {conflict['starts_at']} → {conflict['ends_at']}"
            )
        raise SystemExit("Event was not created because of a conflict.")

    if not args.yes and input("\nCreate this Notion event? [y/N] ").strip().lower() != "y":
        print("Cancelled; nothing was written.")
        return

    event = await agent.create_event(title, start, end, args.notes)
    print(f"Created Notion event: {event.title} ({event.id})")


if __name__ == "__main__":
    asyncio.run(main())
