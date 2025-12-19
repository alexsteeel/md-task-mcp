"""
tm: Simple CLI for markdown-based task management.

Commands:
    tm p,projects        List all projects
    tm t,tasks PROJECT   List tasks for a project
    tm i,init PROJECT    Initialize a new task
    tm o,open PROJECT N  Open task in editor
    tm completion SHELL  Generate shell completion
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

from core import (
    ensure_base_dir,
    find_plan_file,
    get_project_dir,
    list_projects,
    parse_tasks_file,
    slugify,
)


class AliasedGroup(click.Group):
    """Click group that supports command aliases."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aliases: dict[str, str] = {}

    def add_alias(self, name: str, target: str):
        self._aliases[name] = target

    def get_command(self, ctx, cmd_name):
        # Check if it's an alias
        if cmd_name in self._aliases:
            cmd_name = self._aliases[cmd_name]
        return super().get_command(ctx, cmd_name)

    def format_commands(self, ctx, formatter):
        """Write all commands with their aliases."""
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None or cmd.hidden:
                continue

            # Find aliases for this command
            aliases = [a for a, t in self._aliases.items() if t == subcommand]
            if aliases:
                name = f"{','.join(aliases)},{subcommand}"
            else:
                name = subcommand

            help_text = cmd.get_short_help_str(limit=formatter.width)
            commands.append((name, help_text))

        if commands:
            with formatter.section("Commands"):
                formatter.write_dl(commands)




def open_in_editor(file_path: Path, editor: str | None = None) -> int:
    """Open a file in the configured editor."""
    if editor:
        editor_cmd = editor
    else:
        editor_cmd = os.environ.get("EDITOR", os.environ.get("VISUAL", "vi"))

    try:
        subprocess.run([editor_cmd, str(file_path)], check=True)
        return 0
    except FileNotFoundError:
        click.echo(f"Editor '{editor_cmd}' not found.", err=True)
        click.echo("Set EDITOR environment variable or use --editor option.", err=True)
        return 1
    except subprocess.CalledProcessError as e:
        return e.returncode


@click.group(cls=AliasedGroup)
@click.version_option(version="0.1.0", prog_name="tm")
def cli():
    """Simple CLI for markdown-based task management."""
    pass


@cli.command("projects")
def cmd_projects():
    """List all projects."""
    projects = list_projects()

    if not projects:
        click.echo("No projects found.")
        return

    for project in projects:
        click.echo(project)


@cli.command("new")
@click.argument("project")
def cmd_new(project: str):
    """Create a new project."""
    ensure_base_dir()
    project_dir = get_project_dir(project)

    if project_dir.exists():
        click.echo(f"Project '{project}' already exists.", err=True)
        sys.exit(1)

    get_project_dir(project, create=True)
    click.echo(f"Created project: {project}")


@cli.command("tasks")
@click.argument("project")
def cmd_tasks(project: str):
    """List tasks for a project."""
    project_dir = get_project_dir(project)
    tasks_file = project_dir / "tasks.md"

    if not project_dir.exists():
        click.echo(f"Project '{project}' does not exist.", err=True)
        sys.exit(1)

    tasks = parse_tasks_file(tasks_file)

    if not tasks:
        click.echo(f"No tasks found in project '{project}'.")
        return

    status_symbol = {"todo": "[ ]", "work": "[*]", "done": "[x]"}

    for task in tasks:
        symbol = status_symbol.get(task.status, "[ ]")
        click.echo(f"{symbol} #{task.number}: {task.description}")


@cli.command("init")
@click.argument("project")
@click.option("-d", "--description", help="Task description")
@click.option("-e", "--edit", is_flag=True, help="Open in editor after creating")
@click.option("--editor", help="Editor to use (default: $EDITOR)")
def cmd_init(project: str, description: str | None, edit: bool, editor: str | None):
    """Initialize a new task in PROJECT."""
    ensure_base_dir()
    project_dir = get_project_dir(project, create=True)
    tasks_file = project_dir / "tasks.md"

    tasks = parse_tasks_file(tasks_file)
    next_num = max((t.number for t in tasks), default=0) + 1

    if not description:
        description = click.prompt("Short description")

    if not description:
        click.echo("Description cannot be empty.", err=True)
        sys.exit(1)

    task_entry = f"""# {next_num}
description: {description}
worktree:
status: todo
started:
completed:

"""

    with tasks_file.open("a", encoding="utf-8") as f:
        if tasks_file.exists() and tasks_file.stat().st_size > 0:
            content = tasks_file.read_text(encoding="utf-8")
            if not content.endswith("\n\n"):
                f.write("\n" if content.endswith("\n") else "\n\n")
        f.write(task_entry)

    click.echo(f"Created task #{next_num}: {description}")

    if edit:
        sys.exit(open_in_editor(tasks_file, editor))


@cli.command("open")
@click.argument("project")
@click.argument("task_number", type=int, required=False)
@click.option("-p", "--plan", is_flag=True, help="Open plan file (requires task number)")
@click.option("--editor", help="Editor to use (default: $EDITOR)")
def cmd_open(project: str, task_number: int | None, plan: bool, editor: str | None):
    """Open project tasks or plan file in editor."""
    project_dir = get_project_dir(project)

    if not project_dir.exists():
        click.echo(f"Project '{project}' does not exist.", err=True)
        sys.exit(1)

    tasks_file = project_dir / "tasks.md"

    if plan:
        if task_number is None:
            click.echo("Task number required with -p/--plan flag.", err=True)
            sys.exit(1)

        tasks = parse_tasks_file(tasks_file)
        target_task = None
        for task in tasks:
            if task.number == task_number:
                target_task = task
                break

        if target_task is None:
            click.echo(f"Task #{task_number} not found.", err=True)
            sys.exit(1)

        plan_file = find_plan_file(project_dir, task_number)
        if plan_file is None:
            slug = slugify(target_task.description) or "untitled"
            filename = f"task-{task_number}-{slug}.md"
            plans_dir = project_dir / "plans"
            plans_dir.mkdir(exist_ok=True)
            plan_file = plans_dir / filename
            plan_file.write_text(
                f"# Task #{task_number}: {target_task.description}\n\n",
                encoding="utf-8"
            )
            click.echo(f"Created plan file: {plan_file}")
        file_to_open = plan_file
    else:
        file_to_open = tasks_file

    sys.exit(open_in_editor(file_to_open, editor))


@cli.command("completion")
@click.argument("shell", type=click.Choice(["zsh", "bash"]))
@click.option("--install", is_flag=True, help="Install completion to shell config")
def cmd_completion(shell: str, install: bool):
    """Generate shell completion script."""
    if install:
        if shell == "zsh":
            zfunc_dir = Path.home() / ".zfunc"
            zfunc_dir.mkdir(exist_ok=True)
            completion_file = zfunc_dir / "_tm"
            completion_file.write_text(ZSH_COMPLETION, encoding="utf-8")
            click.echo(f"Installed completion to {completion_file}")
            click.echo("\nAdd this to your ~/.zshrc (if not already present):")
            click.echo('  fpath+=~/.zfunc; autoload -Uz compinit; compinit')
            click.echo("\nThen restart your shell: exec zsh")
        elif shell == "bash":
            bash_comp_dir = Path.home() / ".local" / "share" / "bash-completion" / "completions"
            bash_comp_dir.mkdir(parents=True, exist_ok=True)
            completion_file = bash_comp_dir / "tm"
            completion_file.write_text(BASH_COMPLETION, encoding="utf-8")
            click.echo(f"Installed completion to {completion_file}")
            click.echo("\nRestart your shell to enable completion.")
    else:
        if shell == "zsh":
            click.echo(ZSH_COMPLETION)
        elif shell == "bash":
            click.echo(BASH_COMPLETION)


# Register aliases
cli.add_alias("p", "projects")
cli.add_alias("n", "new")
cli.add_alias("t", "tasks")
cli.add_alias("i", "init")
cli.add_alias("o", "open")
cli.add_alias("e", "open")


ZSH_COMPLETION = r'''#compdef tm

_tm() {
    local curcontext="$curcontext" state line
    typeset -A opt_args
    local base_dir="$HOME/.md-task-mcp"

    _arguments -C \
        '1: :->command' \
        '*: :->args'

    case $state in
        command)
            local commands=(
                'p:List all projects'
                'projects:List all projects'
                'n:Create new project'
                'new:Create new project'
                't:List tasks for a project'
                'tasks:List tasks for a project'
                'i:Initialize a new task'
                'init:Initialize a new task'
                'o:Open in editor'
                'e:Open in editor'
                'open:Open in editor'
                'completion:Generate shell completion'
            )
            _describe 'command' commands
            ;;
        args)
            case $line[1] in
                t|tasks|i|init|o|e|open)
                    if [[ $CURRENT -eq 3 ]]; then
                        local projects=()
                        [[ -d "$base_dir" ]] && projects=($(ls -1 "$base_dir" 2>/dev/null))
                        _describe 'project' projects
                    elif [[ $CURRENT -eq 4 && ($line[1] == o || $line[1] == e || $line[1] == open) ]]; then
                        local project=$line[2]
                        local tasks_file="$base_dir/$project/tasks.md"
                        local tasks=()
                        [[ -f "$tasks_file" ]] && tasks=($(grep -oP '^# \K\d+' "$tasks_file" 2>/dev/null))
                        _describe 'task' tasks
                    fi
                    ;;
                completion)
                    if [[ $CURRENT -eq 3 ]]; then
                        local shells=(zsh bash)
                        _describe 'shell' shells
                    fi
                    ;;
            esac
            ;;
    esac
}

_tm "$@"
'''

BASH_COMPLETION = r'''_tm() {
    local cur prev words cword
    _init_completion || return

    local base_dir="$HOME/.md-task-mcp"
    local commands="p projects n new t tasks i init o e open completion"

    if [[ $cword -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return
    fi

    local cmd="${words[1]}"

    case $cmd in
        t|tasks|i|init|o|e|open)
            if [[ $cword -eq 2 ]]; then
                local projects=""
                [[ -d "$base_dir" ]] && projects=$(ls -1 "$base_dir" 2>/dev/null)
                COMPREPLY=($(compgen -W "$projects" -- "$cur"))
            elif [[ $cword -eq 3 && ($cmd == o || $cmd == e || $cmd == open) ]]; then
                local project="${words[2]}"
                local tasks_file="$base_dir/$project/tasks.md"
                local tasks=""
                [[ -f "$tasks_file" ]] && tasks=$(grep -oP '^# \K\d+' "$tasks_file" 2>/dev/null)
                COMPREPLY=($(compgen -W "$tasks" -- "$cur"))
            fi
            ;;
        completion)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "zsh bash" -- "$cur"))
            fi
            ;;
    esac
}

complete -F _tm tm
'''


def main() -> int:
    """Main entry point."""
    cli()
    return 0


if __name__ == "__main__":
    sys.exit(main())
