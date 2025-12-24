# md-task-mcp

Markdown-based task management MCP server and CLI for Claude Code.

## Installation

```bash
uv tool install /path/to/md-task-mcp
```

## CLI Usage

### Project Commands

```bash
tm p                    # List all projects
tm p list               # List all projects
tm p ls                 # List all projects
tm p add <name>         # Create a new project
```

### Task Commands

```bash
tm t                    # Tree view of all projects and tasks
tm t list               # Tree view of all projects and tasks
tm t ls                 # Tree view of all projects and tasks
tm t list <project>     # List tasks in specific project
tm t list <project> <n> # Show task #n details
tm t add                # Add task (prompts for project)
tm t add <project>      # Add task to project
tm t show <project> <n> # Show task #n details
tm t open <project>     # Open task in editor (prompts for task)
tm t open <project> <n> # Open task #n in editor
```

### Shell Completion

```bash
tm completion zsh --install
# Add to ~/.zshrc: fpath+=~/.zfunc; autoload -Uz compinit; compinit
```

## Claude Code Skill

```bash
# Global
cp -r skills/task-manager ~/.claude/skills/

# Or project-specific
cp -r skills/task-manager .claude/skills/
```

## MCP Server Configuration

```bash
# Global
claude mcp add --scope user md-task-mcp -- md-task-mcp

# Or project-specific
claude mcp add md-task-mcp -- md-task-mcp
```

## MCP Tools

- `list_projects` - List all projects
- `list_tasks` - List tasks for a project
- `read_task` - Read full task details including plan
- `read_plan` - Read implementation plan
- `write_requirements` - Write/update task plan
- `update_task` - Update task fields (status, worktree, dates)
- `create_task` - Create a new task

## File Structure

```
~/.md-task-mcp/
├── project-name/
│   └── tasks/
│       ├── 001-implement-auth.md
│       ├── 002-fix-login-bug.md
│       └── ...
```

## Task File Format

Each task is a single markdown file (`~/.md-task-mcp/{project}/tasks/NNN-slug.md`):

```markdown
# Task 1: Implement user authentication
status: work
worktree: /path/to/worktree
started: 2025-01-15
completed:

## Description
Detailed description of the task.

## Plan
Implementation plan and requirements here.
```

## License

MIT
