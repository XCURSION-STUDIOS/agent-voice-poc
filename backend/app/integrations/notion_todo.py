"""Notion adapter for the embedded Todo List database."""

from __future__ import annotations

from datetime import datetime
from typing import Any
import asyncio

from app.agents.task_agent import Task
from app.integrations.notion_calendar import _request_json


class NotionTodoStore:
    def __init__(self, api_key: str, database_id: str, data_source_id: str) -> None:
        self.database_id = database_id
        self.data_source_id = data_source_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2026-03-11",
            "Content-Type": "application/json",
        }

    async def list_tasks(self, status: str | None = None) -> list[Task]:
        payload: dict[str, Any] = {"page_size": 100}
        if status:
            payload["filter"] = {"property": "Status", "status": {"equals": status}}
        body = await self._request(
            "POST", f"https://api.notion.com/v1/data_sources/{self.data_source_id}/query", payload
        )
        return [_page_to_task(page) for page in body.get("results", [])]

    async def create_task(self, title: str, **kwargs) -> Task:
        properties = _properties(title=title, **kwargs)
        page = await self._request(
            "POST",
            "https://api.notion.com/v1/pages",
            {"parent": {"database_id": self.database_id}, "properties": properties},
        )
        return _page_to_task(page)

    async def update_task(self, task_id: str, **kwargs) -> Task:
        properties = _properties(**kwargs)
        page = await self._request("PATCH", f"https://api.notion.com/v1/pages/{task_id}", {"properties": properties})
        return _page_to_task(page)

    async def archive_task(self, task_id: str) -> None:
        await self._request("PATCH", f"https://api.notion.com/v1/pages/{task_id}", {"in_trash": True})

    async def add_note(self, task_id: str, note: str) -> None:
        page = await self._request("GET", f"https://api.notion.com/v1/pages/{task_id}", None)
        current = page.get("properties", {}).get("Details", {}).get("rich_text", [])
        old = " ".join(item.get("plain_text", "") for item in current).strip()
        details = f"{old}\n{note}".strip() if old else note
        await self._request(
            "PATCH",
            f"https://api.notion.com/v1/pages/{task_id}",
            {"properties": {"Details": {"rich_text": [{"type": "text", "text": {"content": details}}]}}},
        )

    async def _request(self, method: str, url: str, payload: dict[str, Any] | None):
        return await asyncio.to_thread(_request_json, method, url, self.headers, payload)


def _properties(**values: Any) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    if values.get("title") is not None:
        properties["Task name"] = {"title": [{"text": {"content": values["title"]}}]}
    if values.get("status") is not None:
        properties["Status"] = {"status": {"name": values["status"]}}
    if values.get("details") is not None:
        properties["Details"] = {"rich_text": [{"type": "text", "text": {"content": values["details"]}}]}
    if values.get("due_date") is not None:
        value = values["due_date"].isoformat() if isinstance(values["due_date"], datetime) else values["due_date"]
        properties["Due date"] = {"date": {"start": value}}
    if values.get("priority") is not None:
        properties["Priority"] = {"select": {"name": values["priority"]}}
    if values.get("project") is not None:
        properties["Category/Project"] = {"rich_text": [{"type": "text", "text": {"content": values["project"]}}]}
    if values.get("estimated_minutes") is not None:
        properties["Estimated time"] = {"number": values["estimated_minutes"]}
    return properties


def _page_to_task(page: dict[str, Any]) -> Task:
    properties = page.get("properties", {})
    title = "".join(item.get("plain_text", "") for item in properties.get("Task name", {}).get("title", []))
    due = properties.get("Due date", {}).get("date") or {}
    return Task(
        id=page["id"],
        title=title or "Untitled",
        status=(properties.get("Status", {}).get("status") or {}).get("name", "Not started"),
        due_date=datetime.fromisoformat(due["start"].replace("Z", "+00:00")) if due.get("start") else None,
        details=" ".join(item.get("plain_text", "") for item in properties.get("Details", {}).get("rich_text", [])) or None,
        priority=(properties.get("Priority", {}).get("select") or {}).get("name"),
    )
