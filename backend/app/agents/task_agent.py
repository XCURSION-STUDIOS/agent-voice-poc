"""Task specialist independent from the voice pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class Task:
    id: str
    title: str
    status: str
    due_date: datetime | None = None
    details: str | None = None
    priority: str | None = None


class TaskStore(Protocol):
    async def list_tasks(self, status: str | None = None) -> list[Task]: ...

    async def create_task(self, title: str, **kwargs) -> Task: ...

    async def update_task(self, task_id: str, **kwargs) -> Task: ...

    async def archive_task(self, task_id: str) -> None: ...

    async def add_note(self, task_id: str, note: str) -> None: ...


class TaskAgent:
    def __init__(self, store: TaskStore) -> None:
        self.store = store

    async def find(self, status: str | None = None) -> list[Task]:
        return await self.store.list_tasks(status)

    async def create(self, title: str, **kwargs) -> Task:
        return await self.store.create_task(title, **kwargs)

    async def update(self, task_id: str, **kwargs) -> Task:
        return await self.store.update_task(task_id, **kwargs)

    async def complete(self, task_id: str) -> Task:
        return await self.store.update_task(task_id, status="Done")

    async def archive(self, task_id: str) -> None:
        await self.store.archive_task(task_id)

    async def note(self, task_id: str, note: str) -> None:
        await self.store.add_note(task_id, note)


@dataclass
class InMemoryTaskStore:
    tasks: list[Task] = field(default_factory=list)

    async def list_tasks(self, status: str | None = None) -> list[Task]:
        return [task for task in self.tasks if status is None or task.status == status]

    async def create_task(self, title: str, **kwargs) -> Task:
        task = Task(id=f"local-task-{len(self.tasks) + 1}", title=title, status="Not started", **kwargs)
        self.tasks.append(task)
        return task

    async def update_task(self, task_id: str, **kwargs) -> Task:
        task = next(task for task in self.tasks if task.id == task_id)
        for key, value in kwargs.items():
            if value is not None and hasattr(task, key):
                setattr(task, key, value)
        return task

    async def archive_task(self, task_id: str) -> None:
        self.tasks = [task for task in self.tasks if task.id != task_id]

    async def add_note(self, task_id: str, note: str) -> None:
        task = next(task for task in self.tasks if task.id == task_id)
        task.details = f"{task.details}\n{note}".strip() if task.details else note
