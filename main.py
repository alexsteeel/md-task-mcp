"""
MD-Task-MCP: Markdown-based task management MCP server for Claude Code.

Folder structure:
~/.md-task-mcp/
├── project-name/
│   ├── tasks.md           # Main tasks file
│   └── plans/
│       └── task-{N}-{slug}.md  # Requirements files
"""

from __future__ import annotations

from fastmcp import FastMCP

from core import (
    BASE_DIR,
    VALID_STATUSES,
    get_project_dir,
    slugify,
    parse_tasks_file,
    write_tasks_file,
    find_plan_file,
    list_projects as _list_projects,
)

# Initialize FastMCP server
mcp = FastMCP("md-task-mcp")


@mcp.tool
def list_projects() -> list[str]:
    """
    List all projects in the task management system.

    Returns a list of project names (folder names in ~/.md-task-mcp).
    """
    return _list_projects()


@mcp.tool
def list_tasks(project: str) -> list[dict]:
    """
    List all tasks for a given project.

    Args:
        project: Name of the project

    Returns:
        List of task summaries with number, short_description, and status
    """
    project_dir = get_project_dir(project)
    tasks_file = project_dir / "tasks.md"

    if not project_dir.exists():
        raise ValueError(f"Project '{project}' does not exist")

    tasks = parse_tasks_file(tasks_file)
    return [
        {
            "number": t.number,
            "description": t.description,
            "status": t.status,
        }
        for t in tasks
    ]


@mcp.tool
def read_task(project: str, task_number: int) -> dict:
    """
    Read full details of a specific task.

    Args:
        project: Name of the project
        task_number: Task number to read

    Returns:
        Full task details including description
    """
    project_dir = get_project_dir(project)
    tasks_file = project_dir / "tasks.md"

    if not project_dir.exists():
        raise ValueError(f"Project '{project}' does not exist")

    tasks = parse_tasks_file(tasks_file)
    for task in tasks:
        if task.number == task_number:
            return task.to_dict()

    raise ValueError(f"Task #{task_number} not found in project '{project}'")


@mcp.tool
def read_plan(project: str, task_number: int) -> str | None:
    """
    Read the implementation requirements/plan for a task.

    Args:
        project: Name of the project
        task_number: Task number to read plan for

    Returns:
        Plan content as string, or None if no plan exists
    """
    project_dir = get_project_dir(project)

    if not project_dir.exists():
        raise ValueError(f"Project '{project}' does not exist")

    plan_file = find_plan_file(project_dir, task_number)
    if plan_file is None:
        return None

    return plan_file.read_text(encoding="utf-8")


@mcp.tool
def write_requirements(project: str, task_number: int, content: str) -> str:
    """
    Write or update implementation requirements for a task.

    The task must already exist in tasks.md. Creates the plan file
    at plans/task-{number}-{slug}.md where slug is derived from
    the task's short_description.

    Args:
        project: Name of the project
        task_number: Task number to write requirements for
        content: The requirements/plan content to write

    Returns:
        Path to the created/updated plan file
    """
    project_dir = get_project_dir(project, create=True)
    tasks_file = project_dir / "tasks.md"

    # Verify task exists
    tasks = parse_tasks_file(tasks_file)
    target_task = None
    for task in tasks:
        if task.number == task_number:
            target_task = task
            break

    if target_task is None:
        raise ValueError(
            f"Task #{task_number} not found in project '{project}'. "
            "Create the task in tasks.md first."
        )

    # Generate filename
    slug = slugify(target_task.description) or "untitled"
    filename = f"task-{task_number}-{slug}.md"

    # Ensure plans directory exists
    plans_dir = project_dir / "plans"
    plans_dir.mkdir(exist_ok=True)

    # Remove old plan file if slug changed
    old_plan = find_plan_file(project_dir, task_number)
    if old_plan and old_plan.name != filename:
        old_plan.unlink()

    # Write new plan file
    plan_path = plans_dir / filename
    plan_path.write_text(content, encoding="utf-8")

    return str(plan_path)


@mcp.tool
def update_task(
    project: str,
    task_number: int,
    status: str | None = None,
    worktree: str | None = None,
    started: str | None = None,
    completed: str | None = None,
) -> dict:
    """
    Update task fields.

    Args:
        project: Name of the project
        task_number: Task number to update
        status: New status (todo, work, done)
        worktree: Git worktree path
        started: Started date (YYYY-MM-DD)
        completed: Completed date (YYYY-MM-DD)

    Returns:
        Updated task details
    """
    project_dir = get_project_dir(project)
    tasks_file = project_dir / "tasks.md"

    if not project_dir.exists():
        raise ValueError(f"Project '{project}' does not exist")

    if status and status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

    tasks = parse_tasks_file(tasks_file)
    for task in tasks:
        if task.number == task_number:
            if status:
                task.status = status
            if worktree is not None:
                task.worktree = worktree if worktree else None
            if started is not None:
                task.started = started if started else None
            if completed is not None:
                task.completed = completed if completed else None
            write_tasks_file(tasks_file, tasks)
            return task.to_dict()

    raise ValueError(f"Task #{task_number} not found in project '{project}'")


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
