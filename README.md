# md-task-mcp

Markdown-based task management MCP server and CLI for Claude Code.

## Installation

```bash
uv tool install /path/to/md-task-mcp
```

## CLI Usage

```bash
tm p              # list projects
tm n my-project   # create project
tm t my-project   # list tasks
tm i my-project   # create task
tm o my-project   # open tasks.md in editor
tm o my-project 1 -p  # open plan for task #1
```

### Shell Completion

```bash
tm completion zsh --install
# Add to ~/.zshrc: fpath+=~/.zfunc; autoload -Uz compinit; compinit
```

## MCP Tools

- `list_projects` - List all projects
- `list_tasks` - List tasks for a project
- `read_task` - Read full task details
- `read_plan` - Read implementation plan
- `write_requirements` - Write/update task plan
- `update_task` - Update task fields

## Task Format

Tasks stored in `~/.md-task-mcp/{project}/tasks.md`:

```
# 1
description: Task summary
worktree: /path/to/worktree
status: todo
started: 2024-01-15
completed:

Detailed description here.
```

## License

MIT
