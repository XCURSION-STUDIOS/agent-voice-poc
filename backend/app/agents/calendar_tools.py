"""Pipecat function-calling tools exposed by the calendar specialist."""

from __future__ import annotations

from datetime import datetime

from pipecat.services.llm_service import FunctionCallParams

from app.agents.calendar_agent import CalendarAgent


def build_calendar_tools(agent: CalendarAgent):
    """Build per-session tools so state never leaks between voice sessions."""

    async def get_schedule(params: FunctionCallParams, start: str, end: str):
        """Read calendar events in an ISO-8601 time range."""
        events = await agent.schedule(datetime.fromisoformat(start), datetime.fromisoformat(end))
        await params.result_callback(
            {
                "events": [
                    {
                        "id": event.id,
                        "title": event.title,
                        "starts_at": event.starts_at.isoformat(),
                        "ends_at": event.ends_at.isoformat(),
                        "status": event.status,
                    }
                    for event in events
                ]
            }
        )

    async def propose_calendar_event(
        params: FunctionCallParams,
        title: str,
        starts_at: str,
        ends_at: str,
        notes: str | None = None,
    ):
        """Check a new calendar event for conflicts without changing the calendar."""
        result = await agent.propose_event(
            title, datetime.fromisoformat(starts_at), datetime.fromisoformat(ends_at), notes
        )
        await params.result_callback(result)

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

        event = await agent.create_event(
            title, datetime.fromisoformat(starts_at), datetime.fromisoformat(ends_at), notes
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

    return [get_schedule, propose_calendar_event, create_calendar_event]
