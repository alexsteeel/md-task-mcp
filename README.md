# md-task-mcp

Markdown-based task management MCP server and CLI for Claude Code.

## Installation

```bash
uv tool install /path/to/md-task-mcp
```

Ensure `~/.local/bin` is in your PATH:

```bash
# bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

# zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
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

## Web UI

```bash
tm-web
```

Open http://localhost:8080 in browser.

Views:
- `/` - Projects cloud
- `/project/{name}` - Tasks cloud view
- `/kanban/{name}` - Kanban board view

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

## MCP Tools (3 optimized tools)

### `tasks` - Universal Read
```
tasks()                    # List all projects with task summaries
tasks("my-project")        # List tasks in project
tasks("my-project", 1)     # Get full task details including plan
```

### `create_task` - Create
```
create_task(project, description, body?, plan?)
```

### `update_task` - Update Any Field
```
update_task(project, number, description?, status?, plan?, body?, report?, review?, blocks?, module?, branch?, started?, completed?, depends_on?)
```

### Attachments Tools

```
list_attachments(project, number)           # List attachments with paths
add_attachment(project, number, source_path, filename?)  # Copy file to attachments
delete_attachment(project, number, filename)  # Delete attachment
```

To read attachment content, use Claude's Read tool with the path from `list_attachments`.

## File Structure

```
~/.md-task-mcp/
├── project-name/
│   └── tasks/
│       ├── 001-implement-auth.md
│       ├── 001-implement-auth/     # attachments folder
│       │   ├── screenshot.png
│       │   └── design.pdf
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
