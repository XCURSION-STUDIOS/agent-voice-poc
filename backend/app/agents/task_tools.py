"""Pipecat tools exposed by the Todo specialist."""

from __future__ import annotations

from datetime import datetime

from pipecat.services.llm_service import FunctionCallParams

from app.agents.task_agent import TaskAgent


def build_task_tools(agent: TaskAgent):
    async def find_tasks(params: FunctionCallParams, status: str | None = None):
        """Find tasks in the Todo List. Status may be Not started, In progress, or Done."""
        tasks = await agent.find(status)
        await params.result_callback({"tasks": [_task_dict(task) for task in tasks]})

    async def add_task(
        params: FunctionCallParams,
        title: str,
        details: str | None = None,
        due_date: str | None = None,
        priority: str | None = None,
        project: str | None = None,
        estimated_minutes: int | None = None,
    ):
        """Add a task to the Todo List."""
        task = await agent.create(
            title,
            details=details,
            due_date=_parse_date(due_date),
            priority=priority,
            project=project,
            estimated_minutes=estimated_minutes,
        )
        await params.result_callback({"status": "created", "task": _task_dict(task)})

    async def update_task(
        params: FunctionCallParams,
        task_id: str,
        title: str | None = None,
        details: str | None = None,
        due_date: str | None = None,
        priority: str | None = None,
        status: str | None = None,
    ):
        """Modify a task after identifying it with find_tasks."""
        task = await agent.update(
            task_id,
            title=title,
            details=details,
            due_date=_parse_date(due_date),
            priority=priority,
            status=status,
        )
        await params.result_callback({"status": "updated", "task": _task_dict(task)})

    async def complete_task(params: FunctionCallParams, task_id: str, confirmed: bool = False):
        """Mark a task Done. Requires explicit user confirmation."""
        if not confirmed:
            await params.result_callback({"status": "confirmation_required"})
            return
        task = await agent.complete(task_id)
        await params.result_callback({"status": "completed", "task": _task_dict(task)})

    async def remove_task(params: FunctionCallParams, task_id: str, confirmed: bool = False):
        """Archive a task. Requires explicit user confirmation."""
        if not confirmed:
            await params.result_callback({"status": "confirmation_required"})
            return
        await agent.archive(task_id)
        await params.result_callback({"status": "archived", "task_id": task_id})

    async def add_task_note(params: FunctionCallParams, task_id: str, note: str):
        """Add a note to a task's Details field."""
        await agent.note(task_id, note)
        await params.result_callback({"status": "note_added", "task_id": task_id})

    return [find_tasks, add_task, update_task, complete_task, remove_task, add_task_note]


def _parse_date(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _task_dict(task) -> dict[str, object]:
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "details": task.details,
        "priority": task.priority,
    }
