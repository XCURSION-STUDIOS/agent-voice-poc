"""Test the Notion-backed Todo agent without starting the voice bot.

Examples:
    uv run python -m scripts.test_task_agent list
    uv run python -m scripts.test_task_agent create --title "Buy groceries"
    uv run python -m scripts.test_task_agent complete --task-id PAGE_ID
    uv run python -m scripts.test_task_agent note --task-id PAGE_ID --note "Buy oat milk"
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from app.agents.task_agent import TaskAgent
from app.config.settings import get_settings
from app.integrations.notion_todo import NotionTodoStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test the Notion-backed Todo agent")
    subparsers = parser.add_subparsers(dest="action", required=True)

    list_parser = subparsers.add_parser("list", help="List Todo items")
    list_parser.add_argument("--status", help="Filter by status")

    create_parser = subparsers.add_parser("create", help="Create a Todo item")
    create_parser.add_argument("--title", required=True)
    create_parser.add_argument("--details")
    create_parser.add_argument("--due-date", help="ISO-8601 date or datetime")
    create_parser.add_argument("--priority", choices=["Low", "Medium", "High"])
    create_parser.add_argument("--project")
    create_parser.add_argument("--estimated-minutes", type=int)

    for name in ("complete", "archive"):
        action_parser = subparsers.add_parser(name, help=f"{name.title()} a Todo item")
        action_parser.add_argument("--task-id", required=True)
        action_parser.add_argument("--yes", action="store_true")

    note_parser = subparsers.add_parser("note", help="Add to a Todo item's Details")
    note_parser.add_argument("--task-id", required=True)
    note_parser.add_argument("--note", required=True)
    return parser.parse_args()


async def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    settings = get_settings()
    if not settings.notion_api_key:
        raise SystemExit("Set NOTION_API_KEY in backend/.env first.")

    args = parse_args()
    if hasattr(args, "task_id"):
        args.task_id = args.task_id.strip().strip("()")
    store = NotionTodoStore(
        settings.notion_api_key.get_secret_value(),
        settings.notion_todo_database_id,
        settings.notion_todo_data_source_id,
    )
    agent = TaskAgent(store)

    if args.action == "list":
        tasks = await agent.find(args.status)
        if not tasks:
            print("No tasks found.")
            return
        for task in tasks:
            due = f" | due {task.due_date.isoformat()}" if task.due_date else ""
            print(f"{task.id} | {task.status} | {task.title}{due}")
        return

    if args.action == "create":
        task = await agent.create(
            args.title,
            details=args.details,
            due_date=_parse_date(args.due_date),
            priority=args.priority,
            project=args.project,
            estimated_minutes=args.estimated_minutes,
        )
        print(f"Created: {task.title} ({task.id})")
        return

    if args.action == "note":
        await agent.note(args.task_id, args.note)
        print(f"Added note to {args.task_id}")
        return

    if not args.yes and input(f"{args.action.title()} {args.task_id}? [y/N] ").strip().lower() != "y":
        print("Cancelled; nothing was changed.")
        return

    if args.action == "complete":
        task = await agent.complete(args.task_id)
        print(f"Completed: {task.title}")
    else:
        await agent.archive(args.task_id)
        print(f"Archived: {args.task_id}")


def _parse_date(value: str | None):
    from datetime import datetime

    return datetime.fromisoformat(value) if value else None


if __name__ == "__main__":
    asyncio.run(main())
