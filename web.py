"""Simple web UI for task cloud visualization."""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

from core import list_projects, list_tasks, read_task, write_task

app = FastAPI(title="Task Cloud")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


class TaskUpdate(BaseModel):
    body: Optional[str] = None
    plan: Optional[str] = None
    report: Optional[str] = None
    review: Optional[str] = None


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
        "done": [t for t in tasks if t.status == "done"],
    }
    return templates.TemplateResponse("kanban.html", {
        "request": request,
        "project": name,
        "board": board,
    })


@app.post("/api/task/{project}/{number}")
async def update_task(project: str, number: int, data: TaskUpdate):
    """Update task body or plan."""
    task = read_task(project, number)
    if task is None:
        return {"error": "Task not found"}, 404

    if data.body is not None:
        task.body = data.body
    if data.plan is not None:
        task.plan = data.plan
    if data.report is not None:
        task.report = data.report
    if data.review is not None:
        task.review = data.review

    write_task(project, task)
    return {"ok": True}


def main():
    """Run the web server."""
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
