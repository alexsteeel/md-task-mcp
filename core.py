"""
Core utilities for md-task-mcp.

Shared constants, data classes, and functions used by both
the MCP server and CLI tool.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Constants
BASE_DIR = Path.home() / ".md-task-mcp"
VALID_STATUSES = {"todo", "work", "done"}


@dataclass
class Task:
    """Represents a task from tasks.md."""

    number: int
    description: str = ""
    worktree: str | None = None
    status: str = "todo"
    started: str | None = None
    completed: str | None = None
    body: str = ""

    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            "number": self.number,
            "description": self.description,
            "worktree": self.worktree,
            "status": self.status,
            "started": self.started,
            "completed": self.completed,
            "body": self.body.strip(),
        }


def ensure_base_dir() -> Path:
    """Create base directory if it doesn't exist."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    return BASE_DIR


def get_project_dir(project: str, create: bool = False) -> Path:
    """Get project directory path, optionally creating it."""
    project_dir = BASE_DIR / project
    if create:
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "plans").mkdir(exist_ok=True)
    return project_dir


def slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:50].strip("-")


def parse_tasks_file(path: Path) -> list[Task]:
    """
    Parse tasks.md file into list of Task objects.

    Format:
    # 1
    short_description: Some description
    git_worktree: /path/to/worktree
    status: todo
    started_at: 2024-01-01
    completed_at:

    Multiline description here.
    """
    if not path.exists():
        return []

    tasks: list[Task] = []
    current_task: Task | None = None
    in_body = False

    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    task_header_pattern = re.compile(r"^#\s+(\d+)\s*$")
    metadata_pattern = re.compile(r"^(\w+):\s*(.*)$")

    for line in lines:
        # Check for task header
        header_match = task_header_pattern.match(line)
        if header_match:
            # Save previous task
            if current_task is not None:
                tasks.append(current_task)
            # Start new task
            current_task = Task(number=int(header_match.group(1)))
            in_body = False
            continue

        if current_task is None:
            continue

        # Check for metadata line
        if not in_body:
            metadata_match = metadata_pattern.match(line)
            if metadata_match:
                key = metadata_match.group(1)
                value = metadata_match.group(2).strip()
                if key == "description":
                    current_task.description = value
                elif key == "worktree":
                    current_task.worktree = value if value else None
                elif key == "status":
                    current_task.status = value if value in VALID_STATUSES else "todo"
                elif key == "started":
                    current_task.started = value if value else None
                elif key == "completed":
                    current_task.completed = value if value else None
                continue
            elif line.strip() == "":
                # Empty line after metadata -> switch to body
                in_body = True
                continue

        # Body lines
        if in_body or line.strip():
            in_body = True
            current_task.body += line + "\n"

    # Don't forget last task
    if current_task is not None:
        tasks.append(current_task)

    return tasks


def find_plan_file(project_dir: Path, task_num: int) -> Path | None:
    """Find existing plan file for a task number."""
    plans_dir = project_dir / "plans"
    if not plans_dir.exists():
        return None

    pattern = f"task-{task_num}-*.md"
    matches = list(plans_dir.glob(pattern))
    return matches[0] if matches else None


def list_projects() -> list[str]:
    """List all project names."""
    if not BASE_DIR.exists():
        return []

    return sorted([
        d.name
        for d in BASE_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])


def task_to_string(task: Task) -> str:
    """Convert a Task object back to markdown string."""
    lines = [
        f"# {task.number}",
        f"description: {task.description}",
        f"worktree: {task.worktree or ''}",
        f"status: {task.status}",
        f"started: {task.started or ''}",
        f"completed: {task.completed or ''}",
    ]
    if task.body.strip():
        lines.append("")
        lines.append(task.body.rstrip())
    lines.append("")
    return "\n".join(lines)


def write_tasks_file(path: Path, tasks: list[Task]) -> None:
    """Write list of tasks to tasks.md file."""
    content = "\n".join(task_to_string(t) for t in tasks)
    path.write_text(content, encoding="utf-8")
