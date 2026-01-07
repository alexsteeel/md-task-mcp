"""Simple web UI for task cloud visualization."""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

from core import (
    list_projects, list_tasks, read_task, write_task, delete_task,
    get_project_dir, get_next_task_number, Task, VALID_STATUSES
)

app = FastAPI(title="Task Cloud")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


class TaskUpdate(BaseModel):
    body: Optional[str] = None
    plan: Optional[str] = None
    report: Optional[str] = None
    review: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class TaskCreate(BaseModel):
    description: str
    body: Optional[str] = ""
    plan: Optional[str] = ""


class ProjectCreate(BaseModel):
    name: str


@app.get("/", response_class=HTMLResponse)
async def projects_cloud(request: Request):
    """Display projects as a cloud."""
    projects = []
    for name in list_projects():
        tasks = list_tasks(name)
        projects.append({
            "name": name,
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
    if data.description is not None:
        task.description = data.description
    if data.status is not None and data.status in VALID_STATUSES:
        task.status = data.status

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
    return {"ok": True, "name": name}


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


def main():
    """Run the web server."""
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
