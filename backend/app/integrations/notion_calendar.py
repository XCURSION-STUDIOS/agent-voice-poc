"""Notion data-source adapter for the Content Calendar database."""

from __future__ import annotations

import asyncio
import json
from urllib.request import Request, urlopen
from datetime import datetime
from typing import Any

from app.agents.calendar_agent import CalendarEvent


class NotionCalendarStore:
    """Map the Content Calendar database to the calendar store interface."""

    def __init__(
        self,
        api_key: str,
        database_id: str,
        *,
        title_property: str = "Content name",
        date_property: str = "Film date",
        api_version: str = "2026-03-11",
    ) -> None:
        self.database_id = database_id
        self.title_property = title_property
        self.date_property = date_property
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": api_version,
            "Content-Type": "application/json",
        }
        self._data_source_id: str | None = None

    async def list_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        data_source_id = await self._get_data_source_id()
        payload = {
            "filter": {
                "property": self.date_property,
                "date": {
                    "on_or_after": start.isoformat(),
                    "before": end.isoformat(),
                },
            },
            "sorts": [{"property": self.date_property, "direction": "ascending"}],
            "page_size": 100,
        }
        body = await asyncio.to_thread(
            _request_json,
            "POST",
            f"https://api.notion.com/v1/data_sources/{data_source_id}/query",
            self._headers,
            payload,
        )
        events = [_page_to_event(page, self.title_property, self.date_property) for page in body["results"]]
        # Keep the provider-side filter for efficiency, but enforce the range
        # locally as well. This protects us from schema/API-version differences
        # where a data-source query may return broader results than requested.
        return [event for event in events if _overlaps(event, start, end)]

    async def create_event(
        self,
        title: str,
        starts_at: datetime,
        ends_at: datetime,
        notes: str | None = None,
    ) -> CalendarEvent:
        properties: dict[str, Any] = {
            self.title_property: {"title": [{"text": {"content": title}}]},
            self.date_property: {
                "date": {"start": starts_at.isoformat(), "end": ends_at.isoformat()}
            },
        }
        payload: dict[str, Any] = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }
        if notes:
            payload["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": notes}}]},
                }
            ]

        page = await asyncio.to_thread(
            _request_json, "POST", "https://api.notion.com/v1/pages", self._headers, payload
        )
        return _page_to_event(page, self.title_property, self.date_property)

    async def _get_data_source_id(self) -> str:
        if self._data_source_id:
            return self._data_source_id
        response = await asyncio.to_thread(
            _request_json,
            "GET",
            f"https://api.notion.com/v1/databases/{self.database_id}",
            self._headers,
            None,
        )
        data_sources = response.get("data_sources", [])
        if not data_sources:
            raise RuntimeError("The configured Notion database has no data source")
        self._data_source_id = data_sources[0]["id"]
        return self._data_source_id


def _page_to_event(page: dict[str, Any], title_property: str, date_property: str) -> CalendarEvent:
    properties = page.get("properties", {})
    title_data = properties.get(title_property, {}).get("title", [])
    date_data = properties.get(date_property, {}).get("date") or {}
    title = "".join(item.get("plain_text", "") for item in title_data) or "Untitled"
    start = _parse_datetime(date_data.get("start"))
    end = _parse_datetime(date_data.get("end")) or start
    if start is None:
        raise ValueError(f"Notion page {page.get('id')} has no {date_property} value")
    if end is None:
        end = start
    return CalendarEvent(
        id=page["id"],
        title=title,
        starts_at=start,
        ends_at=end,
        notes=page.get("url"),
    )


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _overlaps(event: CalendarEvent, start: datetime, end: datetime) -> bool:
    event_start = event.starts_at
    event_end = event.ends_at
    if event_start.tzinfo is None and start.tzinfo is not None:
        event_start = event_start.replace(tzinfo=start.tzinfo)
        event_end = event_end.replace(tzinfo=start.tzinfo)
    return event_start < end and event_end > start


def _request_json(
    method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None
) -> dict[str, Any]:
    request = Request(
        url,
        method=method,
        headers=headers,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
    )
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))
