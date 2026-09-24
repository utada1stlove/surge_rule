#!/usr/bin/env python3
"""Minimal stdio MCP server providing visual plan/todo lists for Codex.

Uses only the Python standard library. Wire it into Codex with:

    [mcp_servers.todo]
    command = "python3"
    args = ["/path/to/this/file/server.py", "/path/to/state/plans.json"]

Plans are stored as JSON. Task statuses: pending, in_progress, completed.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

SERVER_INFO = {"name": "todo", "version": "0.1.0"}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "plan_create",
        "description": (
            "Create a new plan (todo list). Returns the plan id and the "
            "checklist as markdown; later tasks can be added or marked done."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Plan title."},
                "tasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional initial task titles.",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "plan_add_task",
        "description": "Add one or more tasks to an existing plan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "tasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
            },
            "required": ["plan_id", "tasks"],
        },
    },
    {
        "name": "plan_update_task",
        "description": (
            "Update a task. status may be 'pending', 'in_progress', "
            "'completed', or a boolean (true = completed, false = pending). "
            "note appends a dated note unless replace_note is true."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "task_id": {"type": "string"},
                "status": {
                    "oneOf": [
                        {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                        },
                        {"type": "boolean"},
                    ]
                },
                "note": {"type": "string"},
                "replace_note": {"type": "boolean", "default": False},
            },
            "required": ["plan_id", "task_id"],
        },
    },
    {
        "name": "plan_list",
        "description": (
            "List plans. With no plan_id, list plan summaries. With plan_id, "
            "show the full checklist with checkboxes and strikethrough for "
            "completed items."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"plan_id": {"type": "string"}},
        },
    },
]


class TodoStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.data: dict[str, Any] = {"version": 1, "plans": {}}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and isinstance(raw.get("plans"), dict):
                    self.data = raw
            except (OSError, json.JSONDecodeError):
                # Keep a useable store even if the file is malformed; the next
                # successful write will repair it.
                self.data = {"version": 1, "plans": {}}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)

    @staticmethod
    def now() -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def _new_id(self, plan_id: str) -> str:
        plan = self.data["plans"][plan_id]
        used = {t["id"] for t in plan.get("tasks", [])}
        n = len(used) + 1
        while str(n) in used:
            n += 1
        return str(n)

    def create_plan(self, title: str, tasks: list[str] | None) -> dict[str, Any]:
        plan_id = f"plan-{int(time.time())}"
        plan: dict[str, Any] = {
            "id": plan_id,
            "title": title,
            "created_at": self.now(),
            "updated_at": self.now(),
            "tasks": [],
            "archived": [],
        }
        self.data["plans"][plan_id] = plan
        for title_ in tasks or []:
            self.add_task(plan_id, title_)
        self.save()
        return self.describe(plan_id)

    def add_task(self, plan_id: str, title: str) -> dict[str, Any]:
        plan = self.get_plan(plan_id)
        task = {
            "id": self._new_id(plan_id),
            "title": title,
            "status": "pending",
            "notes": [],
            "created_at": self.now(),
            "updated_at": self.now(),
        }
        plan["tasks"].append(task)
        plan["updated_at"] = self.now()
        self.save()
        return task

    def update_task(
        self,
        plan_id: str,
        task_id: str,
        status: str | bool | None,
        note: str | None,
        replace_note: bool,
    ) -> dict[str, Any]:
        plan = self.get_plan(plan_id)
        task = self.get_task(plan, task_id)
        changed = False
        if status is not None:
            if isinstance(status, bool):
                task["status"] = "completed" if status else "pending"
            else:
                task["status"] = status
            changed = True
        if note:
            if replace_note:
                task["notes"] = [note]
            else:
                task["notes"].append(f"{self.now()} - {note}")
            changed = True
        if changed:
            task["updated_at"] = self.now()
            plan["updated_at"] = self.now()
            self.save()
        return task

    def get_plan(self, plan_id: str) -> dict[str, Any]:
        try:
            return self.data["plans"][plan_id]
        except KeyError as exc:
            raise ValueError(f"Plan not found: {plan_id}") from exc

    @staticmethod
    def get_task(plan: dict[str, Any], task_id: str) -> dict[str, Any]:
        for task in plan.get("tasks", []):
            if task["id"] == task_id:
                return task
        raise ValueError(f"Task {task_id} not found in plan {plan['id']}")

    @staticmethod
    def checklist(plan: dict[str, Any]) -> str:
        lines = [f"## {plan['title']}"]
        for task in plan.get("tasks", []):
            status = task["status"]
            box = "[x]" if status == "completed" else "[ ]"
            marker = "🔄" if status == "in_progress" else " "
            title = task["title"]
            if status == "completed":
                display = f"{box} ~~{title}~~"
                if task.get("notes"):
                    display += f"  ({len(task['notes'])} note(s))"
            elif status == "in_progress":
                display = f"{box} {marker} {title}"
            else:
                display = f"{box} {title}"
            lines.append(f"- {display}  `#{task['id']}`")
        done = sum(t["status"] == "completed" for t in plan.get("tasks", []))
        total = len(plan.get("tasks", []))
        lines.append(f"\nProgress: {done}/{total} completed.")
        return "\n".join(lines)

    def describe(self, plan_id: str) -> dict[str, Any]:
        plan = self.get_plan(plan_id)
        done = sum(t["status"] == "completed" for t in plan.get("tasks", []))
        total = len(plan.get("tasks", []))
        summary = {
            "plan_id": plan_id,
            "title": plan["title"],
            "progress": f"{done}/{total}",
            "checklist": self.checklist(plan),
        }
        return summary


class TodoServer:
    def __init__(self, store: TodoStore) -> None:
        self.store = store

    def _result_text(self, text: str) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": text}]}

    def handle_tools_call(
        self, name: str, arguments: dict[str, Any] | None
    ) -> dict[str, Any]:
        args = arguments or {}
        store = self.store
        if name == "plan_create":
            title = str(args.get("title", "")).strip()
            if not title:
                raise ValueError("title is required")
            tasks = [str(x).strip() for x in (args.get("tasks") or []) if str(x).strip()]
            summary = store.create_plan(title, tasks)
            return self._result_text(
                f"Created plan `{summary['plan_id']}`.\n\n{summary['checklist']}"
            )
        if name == "plan_add_task":
            plan_id = str(args.get("plan_id", "")).strip()
            tasks = [str(x).strip() for x in (args.get("tasks") or []) if str(x).strip()]
            if not tasks:
                raise ValueError("tasks must be a non-empty array of titles")
            added = [store.add_task(plan_id, title) for title in tasks]
            summary = store.describe(plan_id)
            ids = ", ".join(f"#{t['id']}" for t in added)
            return self._result_text(
                f"Added task(s) {ids} to `{plan_id}`.\n\n{summary['checklist']}"
            )
        if name == "plan_update_task":
            plan_id = str(args.get("plan_id", "")).strip()
            task_id = str(args.get("task_id", "")).strip()
            status = args.get("status")
            if status is not None and not isinstance(status, bool):
                status = str(status)
                if status in {"true", "done", "complete", "completed"}:
                    status = "completed"
                elif status in {"false", "open", "not started", "not_started"}:
                    status = "pending"
                elif status not in {"pending", "in_progress", "completed"}:
                    raise ValueError(
                        "status must be pending, in_progress, completed, or boolean"
                    )
            note = str(args.get("note") or "").strip() or None
            task = store.update_task(
                plan_id,
                task_id,
                status,
                note,
                bool(args.get("replace_note", False)),
            )
            summary = store.describe(plan_id)
            return self._result_text(
                f"Updated `{plan_id}` task `#{task_id}` to "
                f"`{task['status']}`.\n\n{summary['checklist']}"
            )
        if name == "plan_list":
            plan_id = str(args.get("plan_id") or "").strip()
            if plan_id:
                summary = store.describe(plan_id)
                return self._result_text(summary["checklist"])
            plans = store.data["plans"]
            if not plans:
                return self._result_text("No plans yet. Use plan_create to start one.")
            lines = ["Plans:"]
            for plan in plans.values():
                done = sum(t["status"] == "completed" for t in plan.get("tasks", []))
                total = len(plan.get("tasks", []))
                lines.append(
                    f"- `{plan['id']}` {plan['title']} "
                    f"({done}/{total} completed)"
                )
            return self._result_text("\n".join(lines))
        raise ValueError(f"Unknown tool: {name}")

    def handle(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        method = msg.get("method")
        ident = msg.get("id")
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": ident,
                "result": {
                    "protocolVersion": msg.get("params", {}).get(
                        "protocolVersion", "2024-11-05"
                    ),
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": SERVER_INFO,
                },
            }
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return {"jsonrpc": "2.0", "id": ident, "result": {}}
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": ident,
                "result": {"tools": TOOLS},
            }
        if method == "tools/call":
            try:
                result = self.handle_tools_call(
                    msg["params"]["name"], msg["params"].get("arguments")
                )
                return {"jsonrpc": "2.0", "id": ident, "result": result}
            except KeyError as exc:
                error = {"code": -32602, "message": f"Missing parameter: {exc}"}
            except ValueError as exc:
                error = {"code": -32602, "message": str(exc)}
            except Exception as exc:  # pragma: no cover - defensive protocol edge
                error = {"code": -32603, "message": str(exc)}
            return {"jsonrpc": "2.0", "id": ident, "error": error}
        if method == "shutdown":
            return {"jsonrpc": "2.0", "id": ident, "result": None}
        return {
            "jsonrpc": "2.0",
            "id": ident,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


def read_message(stream) -> dict[str, Any] | None:
    first = stream.readline()
    if not first:
        return None
    line = first.decode("utf-8", "replace").rstrip("\r\n")
    if line.startswith("Content-Length: "):
        try:
            length = int(line.split(":", 1)[1].strip())
        except ValueError:
            return None
        while True:
            header = stream.readline()
            if not header:
                return None
            if header in (b"\r\n", b"\n"):
                break
        payload = stream.read(length)
        raw = payload.decode("utf-8", "replace")
    else:
        raw = line
    return json.loads(raw)


def main() -> None:
    default_state = str(Path(__file__).resolve().parent / "plans.json")
    state_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.environ.get("CODEX_TODO_STATE", default_state)
    )
    server = TodoServer(TodoStore(state_path))
    while True:
        try:
            msg = read_message(sys.stdin.buffer)
        except (OSError, EOFError, json.JSONDecodeError):
            break
        if msg is None:
            break
        try:
            response = server.handle(msg)
        except Exception as exc:  # pragma: no cover - keep stdio alive
            print(json.dumps({"jsonrpc": "2.0", "error": str(exc)}), file=sys.stderr)
            response = None
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
