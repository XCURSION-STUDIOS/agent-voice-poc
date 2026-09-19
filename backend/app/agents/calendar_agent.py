"""Calendar domain logic kept independent from the voice pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class CalendarEvent:
    id: str
    title: str
    starts_at: datetime
    ends_at: datetime
    status: str = "scheduled"
    notes: str | None = None


class CalendarStore(Protocol):
    async def list_events(self, start: datetime, end: datetime) -> list[CalendarEvent]: ...

    async def create_event(
        self, title: str, starts_at: datetime, ends_at: datetime, notes: str | None = None
    ) -> CalendarEvent: ...


@dataclass
class InMemoryCalendarStore:
    """Safe development store used until a real provider is configured."""

    events: list[CalendarEvent] = field(default_factory=list)

    async def list_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        return sorted(
            [event for event in self.events if event.starts_at < end and event.ends_at > start],
            key=lambda event: event.starts_at,
        )

    async def create_event(
        self, title: str, starts_at: datetime, ends_at: datetime, notes: str | None = None
    ) -> CalendarEvent:
        event = CalendarEvent(
            id=f"local-{len(self.events) + 1}",
            title=title,
            starts_at=starts_at,
            ends_at=ends_at,
            notes=notes,
        )
        self.events.append(event)
        return event


class CalendarAgent:
    """Calendar specialist invoked by the voice assistant through tools."""

    def __init__(self, store: CalendarStore) -> None:
        self.store = store

    async def schedule(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        return await self.store.list_events(start, end)

    async def propose_event(
        self, title: str, starts_at: datetime, ends_at: datetime, notes: str | None = None
    ) -> dict[str, object]:
        conflicts = await self.store.list_events(starts_at, ends_at)
        return {
            "status": "conflict" if conflicts else "ready",
            "title": title,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "conflicts": [_event_to_dict(event) for event in conflicts],
            "notes": notes,
            "requires_confirmation": True,
        }

    async def create_event(
        self, title: str, starts_at: datetime, ends_at: datetime, notes: str | None = None
    ) -> CalendarEvent:
        return await self.store.create_event(title, starts_at, ends_at, notes)


def _event_to_dict(event: CalendarEvent) -> dict[str, str | None]:
    return {
        "id": event.id,
        "title": event.title,
        "starts_at": event.starts_at.isoformat(),
        "ends_at": event.ends_at.isoformat(),
        "status": event.status,
        "notes": event.notes,
    }
