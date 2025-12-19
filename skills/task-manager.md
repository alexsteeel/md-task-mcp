# Task Manager Skill

Use md-task-mcp to manage development tasks.

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_projects` | List all projects |
| `list_tasks` | List tasks for a project |
| `read_task` | Read full task details (includes worktree path) |
| `read_plan` | Read implementation plan |
| `write_requirements` | Write/update task plan |
| `update_task` | Update task fields (status, worktree, started, completed) |

## Task Format

Tasks in `~/.md-task-mcp/{project}/tasks.md`:

```
# 1
description: Task summary
worktree: /path/to/worktree
status: todo
started: 2024-01-15
completed:

Detailed description here.
```

## Workflows

### View Tasks

1. `list_projects` to see available projects
2. `list_tasks` to see tasks and their status
3. `read_task` to get full details including worktree path

### Update Task

Use `update_task` to change status, set dates, or update worktree:
- Set `status` to "work" when starting, "done" when complete
- Set `started` date (YYYY-MM-DD) when beginning work
- Set `completed` date when finished

### Write Plan

Use `write_requirements` to save implementation plan.

Plans stored at: `~/.md-task-mcp/{project}/plans/task-{N}-{slug}.md`

## Working with Worktrees

When task has a `worktree` field set, that's the directory where code changes should be made. Read the task to get the worktree path before starting work.

## Status Values

- `todo` - Not started
- `work` - In progress
- `done` - Completed
