import functools
import json
import os
import random
import shutil
import stat
import sys
from contextlib import contextmanager
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from subprocess import DEVNULL, call, check_call

import typer
from rich.console import Console
from rich.markdown import Markdown

NOTES_CONFIG_FILE = Path("~/.nte_config.json").expanduser()
NOTES_CONFIG_DEFAULT = {
    "notes_dir": Path("~/.ntes").expanduser(),
    "editor": os.environ.get("EDITOR", "vim"),
}
if NOTES_CONFIG_FILE.is_file():
    NOTES_CONFIG = {**NOTES_CONFIG_DEFAULT, **json.loads(NOTES_CONFIG_FILE.read_text())}
else:
    NOTES_CONFIG = NOTES_CONFIG_DEFAULT
NOTE_PATH = Path(NOTES_CONFIG["notes_dir"])
NOTE_PATH.mkdir(parents=True, exist_ok=True)
TODAY = date.today().isoformat()
NOW = datetime.now().isoformat()

app = typer.Typer()


def note_value(key: str) -> str:
    note_file = NOTE_PATH / key
    if not note_file.is_file():
        typer.echo(f"No value stored for {key}!")
        raise typer.Abort()
    return note_file.read_text()


@lru_cache()
def before():
    run_before = NOTES_CONFIG.get("before", "")
    if run_before:
        call(run_before, shell=True, cwd=NOTE_PATH, stdout=DEVNULL, stderr=DEVNULL)


@lru_cache()
def after():
    run_after = NOTES_CONFIG.get("after", "")
    if run_after:
        call(run_after, shell=True, cwd=NOTE_PATH, stdout=DEVNULL, stderr=DEVNULL)


@app.command()
@lru_cache()
def sync():
    sync = NOTES_CONFIG.get("sync", "")
    if sync:
        call(sync, shell=True, cwd=NOTE_PATH, stdout=DEVNULL, stderr=DEVNULL)
    else:
        before()
        after()


@contextmanager
def config_context():
    before()
    yield
    after()


def configured_environment(func):
    @functools.wraps(func)
    def wrapped_function(*args, **kwargs):
        with config_context():
            return func(*args, **kwargs)

    return wrapped_function


@app.command(name="set")
@configured_environment
def _set(key: str, value: str, overwrite: bool = False):
    note_file = NOTE_PATH / key
    if note_file.exists() and not (overwrite or typer.confirm(f"Replace existing note for {key}.")):
        raise typer.Abort()
    note_file.write_text(value)


@app.command()
@configured_environment
def edit(key: str, using: str = NOTES_CONFIG["editor"]):
    call((using, NOTE_PATH / key))


@app.command()
@configured_environment
def more(key: str, value: str, sep: str = "\n"):
    note_file = NOTE_PATH / key
    if not note_file.exists():
        note_file.write_text(value)
    else:
        with note_file.open("a") as note_file:
            note_file.write(sep)
            note_file.write(value)


@app.command()
@configured_environment
def that(value: str):
    more(TODAY, value)


@app.command()
@configured_environment
def book(using: str = NOTES_CONFIG["editor"]):
    edit(TODAY, using=using)


@app.command()
@configured_environment
def today():
    get(TODAY)


@app.command()
@configured_environment
def get(key: str):
    Console().print(Markdown(note_value(key)))


@app.command("random")
@configured_environment
def _random(key: str):
    Console().print(Markdown(random.choice(note_value(key).splitlines())))


@app.command()
@configured_environment
def todo(task: str, key: str = "TODOS"):
    more(key, f"- [ ] {task}")


@app.command()
@configured_environment
def done(task: str, key: str = "TODOS", create: bool = False):
    existing_todos = note_value(key)
    if f"- [ ] {task}" not in existing_todos:
        if create:
            todo(task, key=key)
        else:
            sys.exit(
                f"No task called {task} exists. To create it while marking it done use --create."
            )
    _set(
        key,
        existing_todos.replace(f"- [ ] {task}", f"- [x] {task} (Completed: {NOW})", 1),
        overwrite=True,
    )


@app.command()
@configured_environment
def clear_done(key: str = "TODOS"):
    _set(
        key,
        "\n".join(
            line for line in note_value(key).splitlines() if line and not line.startswith("- [x]")
        ),
        overwrite=True,
    )


@app.command()
@configured_environment
def todo_remove(task: str, key: str = "TODOS"):
    _set(
        key,
        "\n".join(
            line
            for line in note_value(key).splitlines()
            if line and not line.split("] ", 1)[1] == task
        ),
        overwrite=True,
    )


@app.command()
def todos(key: str = "TODOS"):
    before()
    get(key)


@app.command()
@configured_environment
def run(key: str):
    note_file = NOTE_PATH / key
    os.chmod(note_file, os.stat(note_file).st_mode | stat.S_IEXEC)
    call(note_value(key), shell=True)


@app.command()
def recent(amount: int = 10, lines: int = 3):
    before()
    for note_file in sorted(
        [path for path in NOTE_PATH.glob("*") if not path.name.startswith(".")],
        key=os.path.getctime,
        reverse=True,
    )[:amount]:
        if os.access(note_file, os.X_OK):
            typer.secho(note_file.name, bg=typer.colors.GREEN, fg=typer.colors.WHITE)
        else:
            typer.secho(note_file.name, bg=typer.colors.BLUE, fg=typer.colors.WHITE)
        with note_file.open("r") as note_file_handle:
            for index, line in enumerate(note_file_handle.readlines()):
                if index >= lines:
                    typer.secho(
                        f" {index + 1} ", nl=False, fg=typer.colors.WHITE, bg=typer.colors.YELLOW
                    )
                    typer.secho(
                        " ...".ljust(shutil.get_terminal_size().columns - 3),
                        fg=typer.colors.BLACK,
                        bg=typer.colors.WHITE,
                    )
                    break
                else:
                    typer.secho(
                        f" {index + 1} ", nl=False, fg=typer.colors.WHITE, bg=typer.colors.YELLOW
                    )
                    typer.secho(
                        f" {line.rstrip()}".ljust(shutil.get_terminal_size().columns - 3),
                        fg=typer.colors.BLACK,
                        bg=typer.colors.WHITE,
                    )
        typer.echo("")


@app.command()
def ls():
    before()
    for note_file in sorted(
        [path for path in NOTE_PATH.glob("*") if not path.name.startswith(".")],
        key=os.path.getctime,
        reverse=True,
    ):
        if os.access(note_file, os.X_OK):
            typer.secho(note_file.name, fg=typer.colors.GREEN)
        else:
            typer.echo(note_file.name)


@app.command()
@configured_environment
def event(key: str, details: str = ""):
    more(f"{key}_events", value=f"- *{NOW}* {details}".rstrip())


@app.command()
def events(key: str, details: str = ""):
    before()
    for line in reversed(note_value(f"{key}_events").splitlines()):
        typer.echo(line)


@app.command()
@configured_environment
def edit_events(key: str, using: str = NOTES_CONFIG["editor"]):
    edit(f"{key}_events")


@app.command()
@configured_environment
def delete(key: str):
    (NOTE_PATH / key).unlink()


@app.command()
@configured_environment
def grep(text):
    check_call(("grep", "-Ri", text, NOTE_PATH))


@app.command()
@configured_environment
def rg(text):
    check_call(("rg", text, NOTE_PATH))


if __name__ == "__main__":
    app()
