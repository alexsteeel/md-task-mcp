"""Simple web UI for task cloud visualization."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

from core import (
    list_projects, list_tasks, read_task, write_task, delete_task,
    get_project_dir, get_next_task_number, get_project_description,
    set_project_description, Task, VALID_STATUSES,
    list_attachments, add_attachment, get_attachment_path, delete_attachment,
)


def find_templates_dir() -> Path:
    """Find templates directory in various locations."""
    # 1. Local development path (next to this file)
    local = Path(__file__).parent / "templates"
    if local.exists():
        return local

    # 2. Installed data path (sys.prefix/share/md-task-mcp/templates)
    installed = Path(sys.prefix) / "share" / "md-task-mcp" / "templates"
    if installed.exists():
        return installed

    # 3. User install path (~/.local/share/md-task-mcp/templates)
    user_data = Path.home() / ".local" / "share" / "md-task-mcp" / "templates"
    if user_data.exists():
        return user_data

    raise RuntimeError(
        f"Templates directory not found. Searched:\n"
        f"  - {local}\n"
        f"  - {installed}\n"
        f"  - {user_data}"
    )


app = FastAPI(title="Task Cloud")
templates = Jinja2Templates(directory=find_templates_dir())


class TaskUpdate(BaseModel):
    body: Optional[str] = None
    plan: Optional[str] = None
    report: Optional[str] = None
    review: Optional[str] = None
    blocks: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class TaskCreate(BaseModel):
    description: str
    body: Optional[str] = ""
    plan: Optional[str] = ""


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class ProjectUpdate(BaseModel):
    description: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def projects_cloud(request: Request):
    """Display projects as a cloud."""
    projects = []
    for name in list_projects():
        tasks = list_tasks(name)
        projects.append({
            "name": name,
            "description": get_project_description(name),
            "total": len(tasks),
            "work": sum(1 for t in tasks if t.status == "work"),
            "todo": sum(1 for t in tasks if t.status == "todo"),
            "done": sum(1 for t in tasks if t.status == "done"),
            "approved": sum(1 for t in tasks if t.status == "approved"),
        })
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "projects": projects,
    })


@app.get("/project/{name}", response_class=HTMLResponse)
async def tasks_cloud(request: Request, name: str):
    """Display tasks of a project as a cloud."""
    tasks = list_tasks(name)
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "project": name,
        "tasks": tasks,
    })


@app.get("/kanban/{name}", response_class=HTMLResponse)
async def kanban_board(request: Request, name: str):
    """Display tasks as a kanban board."""
    tasks = list_tasks(name)
    board = {
        "hold": [t for t in tasks if t.status == "hold"],
        "todo": [t for t in tasks if t.status == "todo"],
        "work": [t for t in tasks if t.status == "work"],
        "done": sorted([t for t in tasks if t.status == "done"], key=lambda t: (t.completed or '', t.number), reverse=True),
        "approved": sorted([t for t in tasks if t.status == "approved"], key=lambda t: (t.completed or '', t.number), reverse=True),
    }
    return templates.TemplateResponse("kanban.html", {
        "request": request,
        "project": name,
        "board": board,
    })


@app.get("/api/task/{project}/{number}")
async def get_task_endpoint(project: str, number: int):
    """Get task data."""
    task = read_task(project, number)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@app.post("/api/task/{project}/{number}")
async def update_task_endpoint(project: str, number: int, data: TaskUpdate):
    """Update task body, plan, or description."""
    task = read_task(project, number)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if data.body is not None:
        task.body = data.body
    if data.plan is not None:
        task.plan = data.plan
    if data.report is not None:
        task.report = data.report
    if data.review is not None:
        task.review = data.review
    if data.blocks is not None:
        task.blocks = data.blocks
    if data.description is not None:
        task.description = data.description
    if data.status is not None and data.status in VALID_STATUSES:
        old_status = task.status
        task.status = data.status
        # Auto-set started when moving to work
        if data.status == "work" and old_status != "work" and not task.started:
            task.started = datetime.now().strftime("%Y-%m-%d %H:%M")
        # Auto-set completed when moving to done/approved
        if data.status in ("done", "approved") and old_status not in ("done", "approved") and not task.completed:
            task.completed = datetime.now().strftime("%Y-%m-%d %H:%M")

    write_task(project, task)
    return {"ok": True, "task": task.to_dict()}


@app.delete("/api/task/{project}/{number}")
async def delete_task_endpoint(project: str, number: int):
    """Delete a task."""
    if delete_task(project, number):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/project")
async def create_project_endpoint(data: ProjectCreate):
    """Create a new project."""
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name is required")
    # Create project directory
    get_project_dir(name, create=True)
    if data.description:
        set_project_description(name, data.description)
    return {"ok": True, "name": name}


@app.post("/api/project/{name}")
async def update_project_endpoint(name: str, data: ProjectUpdate):
    """Update project description."""
    if data.description is not None:
        set_project_description(name, data.description)
    return {"ok": True, "description": get_project_description(name)}


@app.post("/api/task/{project}")
async def create_task_endpoint(project: str, data: TaskCreate):
    """Create a new task."""
    if not data.description.strip():
        raise HTTPException(status_code=400, detail="Task description is required")

    # Ensure project exists
    get_project_dir(project, create=True)

    task_number = get_next_task_number(project)
    task = Task(
        number=task_number,
        description=data.description.strip(),
        body=data.body or "",
        plan=data.plan or "",
    )

    write_task(project, task)
    return {"ok": True, "number": task_number, "task": task.to_dict()}


# =============================================================================
# Attachments API
# =============================================================================


@app.get("/api/task/{project}/{number}/attachments")
async def list_attachments_endpoint(project: str, number: int):
    """List all attachments for a task."""
    task = read_task(project, number)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"ok": True, "attachments": list_attachments(project, number)}


@app.post("/api/task/{project}/{number}/attachments")
async def upload_attachment_endpoint(project: str, number: int, file: UploadFile = File(...)):
    """Upload an attachment to a task."""
    task = read_task(project, number)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    content = await file.read()
    file_path = add_attachment(project, number, file.filename, content)

    return {
        "ok": True,
        "name": file_path.name,
        "path": str(file_path),
        "size": len(content),
    }


@app.get("/api/task/{project}/{number}/attachments/{filename:path}")
async def download_attachment_endpoint(project: str, number: int, filename: str):
    """Download an attachment."""
    file_path = get_attachment_path(project, number, filename)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@app.delete("/api/task/{project}/{number}/attachments/{filename:path}")
async def delete_attachment_endpoint(project: str, number: int, filename: str):
    """Delete an attachment."""
    if delete_attachment(project, number, filename):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Attachment not found")


def main():
    """Run the web server."""
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
