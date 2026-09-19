import asyncio
from datetime import datetime, timezone

from app.agents.calendar_agent import CalendarAgent, InMemoryCalendarStore


def test_schedule_returns_overlapping_events_in_order():
    asyncio.run(_test_schedule_returns_overlapping_events_in_order())


async def _test_schedule_returns_overlapping_events_in_order():
    store = InMemoryCalendarStore()
    agent = CalendarAgent(store)
    await agent.create_event(
        "Later", datetime(2026, 9, 19, 11, tzinfo=timezone.utc), datetime(2026, 9, 19, 12, tzinfo=timezone.utc)
    )
    await agent.create_event(
        "Earlier", datetime(2026, 9, 19, 9, tzinfo=timezone.utc), datetime(2026, 9, 19, 10, tzinfo=timezone.utc)
    )

    events = await agent.schedule(
        datetime(2026, 9, 19, 8, tzinfo=timezone.utc),
        datetime(2026, 9, 19, 13, tzinfo=timezone.utc),
    )

    assert [event.title for event in events] == ["Earlier", "Later"]


def test_proposal_reports_conflicts_without_writing():
    asyncio.run(_test_proposal_reports_conflicts_without_writing())


async def _test_proposal_reports_conflicts_without_writing():
    store = InMemoryCalendarStore()
    agent = CalendarAgent(store)
    await agent.create_event(
        "Focus", datetime(2026, 9, 19, 10, tzinfo=timezone.utc), datetime(2026, 9, 19, 11, tzinfo=timezone.utc)
    )

    proposal = await agent.propose_event(
        "Meeting",
        datetime(2026, 9, 19, 10, 30, tzinfo=timezone.utc),
        datetime(2026, 9, 19, 11, 30, tzinfo=timezone.utc),
    )

    assert proposal["status"] == "conflict"
    assert proposal["requires_confirmation"] is True
    assert len(store.events) == 1
