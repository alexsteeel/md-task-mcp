"""Simple web UI for task cloud visualization."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

from core import list_projects, list_tasks

app = FastAPI(title="Task Cloud")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


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


def main():
    """Run the web server."""
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
