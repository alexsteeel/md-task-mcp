---
name: task-manager
description: "Manage development tasks via md-task-mcp MCP server. Use when user asks about tasks, projects, or task management."
---

# Task Manager Skill

Use md-task-mcp to manage development tasks.

## Task Naming Rule

Use infinitive form (что сделать?) with brief goal:
- "Добавить справку для пользователей"
- "Исправить ошибку авторизации"
- "Реализовать экспорт в PDF"
- "Обновить зависимости проекта"

## MCP Tools

| Tool | Description |
|------|-------------|
| `tasks()` | List all projects with task counts |
| `tasks(project)` | List tasks in a project |
| `tasks(project, number)` | Get full task details |
| `create_task(project, description, body?, plan?)` | Create a new task |
| `update_task(project, number, ...)` | Update task fields |

## Task File Format

Tasks stored in `~/.md-task-mcp/{project}/tasks/{NNN}-{slug}.md`:

```markdown
# Task 1: Task summary
status: todo
module: auth
branch: feature/task-1-summary
started: 2024-01-15
completed:
depends_on: 2, 3

## Description
Requirements and detailed description here.

## Plan
Implementation plan here.

## Report
Completion report here.

## Review
Code review feedback here.
```

## Task Sections

| Section | Purpose |
|---------|---------|
| Description | Requirements, detailed task description |
| Plan | Implementation plan, approach |
| Report | Work completion report |
| Review | Code review feedback |

## Workflows

### View Tasks

```
tasks()                    # List all projects
tasks("my-project")        # List tasks in project
tasks("my-project", 1)     # Get full task #1 details
```

### Create Task

```
create_task(
    project="my-project",
    description="Add user authentication",
    body="Requirements here...",
    plan="Implementation plan..."
)
```

### Update Task

```
update_task(
    project="my-project",
    number=1,
    status="work",           # todo, work, done
    module="auth",           # area/module name
    started="2024-01-15",
    branch="feature/task-1",
    body="Updated description",
    plan="Updated plan",
    report="Work completed",
    review="LGTM",
    depends_on=[2, 3]
)
```

### Start Working on Task

**IMPORTANT:** When starting work on a task, ALWAYS:
1. Get current git branch: `git branch --show-current`
2. Update task with branch name and status:

```
update_task(
    project="my-project",
    number=1,
    status="work",
    started="YYYY-MM-DD",
    branch="<current-git-branch>"
)
```

This ensures the task is linked to the correct git branch for tracking.

## Status Values

- `todo` - Not started
- `work` - In progress
- `done` - Completed

## Module Field

Use `module` to categorize tasks by area/component:
- `auth` - Authentication/authorization
- `api` - API endpoints
- `ui` - User interface
- `db` - Database
- Custom names as needed

## Web UI

Start web interface: `tm-web`

Views:
- `/` - Projects cloud
- `/project/{name}` - Tasks cloud view
- `/kanban/{name}` - Kanban board view

Features:
- Click task to view Description/Plan/Report/Review tabs
- Edit sections inline with markdown support
- View toggle (Cloud/Kanban)
- Section icons (D/P/R/V) show content status
- Module badge on task cards
- Blocked-by badges showing depends_on tasks
- Drag column borders to resize (saved to localStorage)
