---
name: codex-mcp-todo
description: Give Codex a visible plan/todo tool when the UI has no separate plan window, using a minimal stdio MCP server with markdown checklists and strikethrough for completed tasks. Use when a user asks for a live checklist, plan tracking, or checkable task list in Codex.
---

# Codex MCP Todo

## Background

Codex sessions do not always expose a separate plan window or a checkable
task-list tool. The user still wants a visible workflow: a plan heading,
checkboxes per task, and completed items shown as checked and struck through.

The fix is a small local MCP server over stdio. Codex starts it, discovers
its tools, and the agent calls them from the conversation. No network, no
third-party dependencies, no external service.

This skill is the experience report and the reproducible implementation:
when the same need appears, copy `scripts/mcp_todo_server.py`, wire it into
Codex, restart the extension or open a new session, and verify the tools are
listed.

## Design

The server uses only the Python standard library and JSON-RPC 2.0 over
newline-delimited JSON on stdin/stdout. State lives in a JSON file passed as
the first argument; paths are configurable so each project can keep its own
plan history.

Exposed tools:

- `plan_create(title, tasks?)` - create a plan and show the checklist.
- `plan_add_task(plan_id, tasks)` - append tasks and re-show the plan.
- `plan_update_task(plan_id, task_id, status?, note?)` - mark pending,
  in_progress, or completed; append dated notes.
- `plan_list(plan_id?)` - list plans or show one full checklist.

Checklist rendering makes the state visible in chat:

```markdown
- [ ] 任务A  `#1`
- [ ] 🔄 任务B  `#2`
- [x] ~~任务C~~  `#3`
```

## Install

1. Copy `scripts/mcp_todo_server.py` to a stable path, for example
   `<project>/.codex/mcp-todo/server.py`, and pick a state file such as
   `<project>/.codex/mcp-todo/plans.json`.
2. Register the server:

   Global (available in every project):

   ```toml
   # ~/.codex/config.toml
   [mcp_servers.todo]
   command = "python3"
   args = ["/absolute/path/to/mcp_todo_server.py", "/absolute/path/to/plans.json"]
   ```

   Project-only (`<project>/.codex/config.toml`):

   ```toml
   [mcp_servers.todo]
   command = "python3"
   args = ["/absolute/path/to/mcp_todo_server.py", "/absolute/path/to/plans.json"]
   ```

   Prefer the global config unless the tool must stay inside one repository.
3. Restart the Codex extension or start a new session. MCP tools are loaded
   at session start; editing the config does not hot-load them.

## Verify

Confirm Codex sees the server before trusting it in a real task:

```bash
codex mcp list
codex mcp get todo
```

Then exercise the protocol directly. Send these JSON-RPC lines on stdin and
inspect the responses:

```bash
printf '%s\n' \
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' \
'{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
'{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"plan_create","arguments":{"title":"验证","tasks":["任务A"]}}}' \
 | python3 /path/to/mcp_todo_server.py /tmp/plans-test.json
```

Expected: an `initialize` result, a `tools/list` result with four tools, and
a `tools/call` result containing a markdown checklist.

## Pitfalls

- The agent's own sandbox may mount `.codex` or `~/.codex` read-only. A server
  run inside that sandbox can still answer `tools/list` but fails on `save()`.
  Verify with escalated permissions or from a normal shell; Codex launches
  MCP servers outside the agent sandbox.
- Project `.codex/config.toml` is only loaded for directories Codex treats as
  projects (typically a git repository root). Non-git folders need the global
  `~/.codex/config.toml` entry.
- Do not commit `plans.json`; add it to `.gitignore`.
- After editing `config.toml`, the current session does not see the tools.
  Tell the user to restart the extension or start a new session.

## Appendix: server implementation

`scripts/mcp_todo_server.py` is the tested implementation. It supports
`initialize`, `notifications/initialized`, `ping`, `tools/list`,
`tools/call`, and `shutdown`, with a JSON file store.
