"""Pipecat function-calling tools exposed by the calendar specialist."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from pipecat.services.llm_service import FunctionCallParams

from app.agents.calendar_agent import CalendarAgent


def build_calendar_tools(agent: CalendarAgent, timezone_name: str = "UTC"):
    """Build per-session tools so state never leaks between voice sessions."""

    timezone = ZoneInfo(timezone_name)

    def parse_user_datetime(value: str) -> datetime:
        """Interpret spoken times without offsets in the user's configured timezone."""
        parsed = datetime.fromisoformat(value)
        return parsed.replace(tzinfo=timezone) if parsed.tzinfo is None else parsed

    async def get_current_datetime(params: FunctionCallParams):
        """Return the current date and time in the user's configured timezone."""
        now = datetime.now(timezone)
        await params.result_callback(
            {
                "status": "ok",
                "timezone": timezone_name,
                "iso": now.isoformat(),
                "date": now.strftime("%A, %B %d, %Y").replace(" 0", " "),
                "time": now.strftime("%I:%M %p").lstrip("0"),
            }
        )

    async def get_schedule(params: FunctionCallParams, start: str, end: str):
        """Read calendar events in an ISO-8601 time range."""
        try:
            events = await agent.schedule(parse_user_datetime(start), parse_user_datetime(end))
            await params.result_callback(
                {
                    "status": "ok",
                    "events": [
                        {
                            "id": event.id,
                            "title": event.title,
                            "starts_at": event.starts_at.isoformat(),
                            "ends_at": event.ends_at.isoformat(),
                            "status": event.status,
                        }
                        for event in events
                    ],
                }
            )
        except Exception as exc:
            await params.result_callback(_error_result(exc))

    async def propose_calendar_event(
        params: FunctionCallParams,
        title: str,
        starts_at: str,
        ends_at: str,
        notes: str | None = None,
    ):
        """Check a new calendar event for conflicts without changing the calendar."""
        try:
            result = await agent.propose_event(
                title, parse_user_datetime(starts_at), parse_user_datetime(ends_at), notes
            )
            await params.result_callback(result)
        except Exception as exc:
            await params.result_callback(_error_result(exc))

    async def create_calendar_event(
        params: FunctionCallParams,
        title: str,
        starts_at: str,
        ends_at: str,
        confirmed: bool = False,
        notes: str | None = None,
    ):
        """Create an event only after the user has explicitly confirmed it."""
        if not confirmed:
            await params.result_callback(
                {"status": "confirmation_required", "message": "Ask the user to confirm first."}
            )
            return

        try:
            event = await agent.create_event(
                title, parse_user_datetime(starts_at), parse_user_datetime(ends_at), notes
            )
            await params.result_callback(
                {
                    "status": "created",
                    "id": event.id,
                    "title": event.title,
                    "starts_at": event.starts_at.isoformat(),
                    "ends_at": event.ends_at.isoformat(),
                }
            )
        except Exception as exc:
            await params.result_callback(_error_result(exc))

    return [get_current_datetime, get_schedule, propose_calendar_event, create_calendar_event]


def _error_result(exc: Exception) -> dict[str, str]:
    return {"status": "error", "error": str(exc)}
