"""
MD-Task-MCP: Markdown-based task management MCP server for Claude Code.

Optimized 3-tool design:
- tasks()              - Universal read (list projects, tasks, or get task details)
- create_task()        - Create new task
- update_task()        - Update any task field
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

mcp = FastMCP("md-task-mcp")


@mcp.tool
def tasks(project: str | None = None, number: int | None = None) -> dict | list:
    """
    Universal task query tool.

    Args:
        project: Optional project name to filter by
        number: Optional task number (requires project)

    Returns:
        - tasks() → list of projects with task summaries
        - tasks(project) → list of tasks in project
        - tasks(project, number) → full task details including plan

    Examples:
        tasks()                    # List all projects with task counts
        tasks("my-project")        # List tasks in my-project
        tasks("my-project", 1)     # Get full details of task #1
    """
    # No args: list all projects with task summaries
    if project is None:
        projects = _list_projects()
        result = []
        for proj in projects:
            proj_tasks = _list_tasks(proj)
            result.append({
                "project": proj,
                "task_count": len(proj_tasks),
                "by_status": {
                    "work": sum(1 for t in proj_tasks if t.status == "work"),
                    "todo": sum(1 for t in proj_tasks if t.status == "todo"),
                    "done": sum(1 for t in proj_tasks if t.status == "done"),
                },
                "tasks": [
                    {"number": t.number, "description": t.description, "status": t.status}
                    for t in proj_tasks
                ],
            })
        return result

    # Project specified: check it exists
    project_dir = get_project_dir(project)
    if not project_dir.exists():
        raise ValueError(f"Project '{project}' does not exist")

    # Project only: list tasks in project
    if number is None:
        proj_tasks = _list_tasks(project)
        return [
            {"number": t.number, "description": t.description, "status": t.status}
            for t in proj_tasks
        ]

    # Project + number: get full task details
    task = _read_task(project, number)
    if task is None:
        raise ValueError(f"Task #{number} not found in project '{project}'")

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
        project: Project name (created if doesn't exist)
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


@mcp.tool
def update_task(
    project: str,
    number: int,
    description: str | None = None,
    status: str | None = None,
    plan: str | None = None,
    body: str | None = None,
    worktree: str | None = None,
    started: str | None = None,
    completed: str | None = None,
) -> dict:
    """
    Update any task field.

    Args:
        project: Project name
        number: Task number to update
        description: New short description
        status: New status (todo, work, done)
        plan: New implementation plan content
        body: New detailed description
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

    task = _read_task(project, number)
    if task is None:
        raise ValueError(f"Task #{number} not found in project '{project}'")

    # Update fields if provided
    if description is not None:
        task.description = description
    if status is not None:
        task.status = status
    if plan is not None:
        task.plan = plan
    if body is not None:
        task.body = body
    if worktree is not None:
        task.worktree = worktree if worktree else None
    if started is not None:
        task.started = started if started else None
    if completed is not None:
        task.completed = completed if completed else None

    write_task(project, task)
    return task.to_dict()


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
