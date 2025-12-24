"""
MD-Task-MCP: Markdown-based task management MCP server for Claude Code.

Folder structure:
~/.md-task-mcp/
├── project-name/
│   └── tasks/
│       ├── 001-add-user-auth.md
│       ├── 002-fix-login-bug.md
│       └── ...

Each task file contains metadata, description, and plan in one place.
"""

from __future__ import annotations

from fastmcp import FastMCP

from core import (
    VALID_STATUSES,
    Task,
    get_project_dir,
    get_next_task_number,
    list_tasks as _list_tasks,
    read_task as _read_task,
    write_task,
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
        List of task summaries with number, description, and status
    """
    project_dir = get_project_dir(project)

    if not project_dir.exists():
        raise ValueError(f"Project '{project}' does not exist")

    tasks = _list_tasks(project)
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
    Read full details of a specific task including plan.

    Args:
        project: Name of the project
        task_number: Task number to read

    Returns:
        Full task details including description and plan
    """
    project_dir = get_project_dir(project)

    if not project_dir.exists():
        raise ValueError(f"Project '{project}' does not exist")

    task = _read_task(project, task_number)
    if task is None:
        raise ValueError(f"Task #{task_number} not found in project '{project}'")

    return task.to_dict()


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

    task = _read_task(project, task_number)
    if task is None:
        raise ValueError(f"Task #{task_number} not found in project '{project}'")

    return task.plan if task.plan else None


@mcp.tool
def write_requirements(project: str, task_number: int, content: str) -> str:
    """
    Write or update implementation requirements/plan for a task.

    Args:
        project: Name of the project
        task_number: Task number to write requirements for
        content: The requirements/plan content to write

    Returns:
        Path to the updated task file
    """
    project_dir = get_project_dir(project)

    if not project_dir.exists():
        raise ValueError(f"Project '{project}' does not exist")

    task = _read_task(project, task_number)
    if task is None:
        raise ValueError(f"Task #{task_number} not found in project '{project}'")

    task.plan = content
    task_path = write_task(project, task)

    return str(task_path)


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

    if not project_dir.exists():
        raise ValueError(f"Project '{project}' does not exist")

    if status and status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

    task = _read_task(project, task_number)
    if task is None:
        raise ValueError(f"Task #{task_number} not found in project '{project}'")

    if status:
        task.status = status
    if worktree is not None:
        task.worktree = worktree if worktree else None
    if started is not None:
        task.started = started if started else None
    if completed is not None:
        task.completed = completed if completed else None

    write_task(project, task)
    return task.to_dict()


@mcp.tool
def create_task(
    project: str,
    description: str,
    body: str = "",
    plan: str = "",
) -> dict:
    """
    Create a new task in a project.

    Args:
        project: Name of the project (created if doesn't exist)
        description: Short task description (used in filename)
        body: Optional detailed description
        plan: Optional implementation plan

    Returns:
        Created task details including number and file path
    """
    # Ensure project exists
    get_project_dir(project, create=True)

    task_number = get_next_task_number(project)
    task = Task(
        number=task_number,
        description=description,
        body=body,
        plan=plan,
    )

    task_path = write_task(project, task)

    result = task.to_dict()
    result["file_path"] = str(task_path)
    return result


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
