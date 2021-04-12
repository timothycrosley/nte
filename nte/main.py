import json
import os
import shutil
import stat
from datetime import date, datetime
from pathlib import Path
from subprocess import call

import typer

NOTES_CONFIG_FILE = Path("~/.nte_config.json").expanduser()
NOTES_CONFIG_DEFAULT = {
    "notes_dir": Path("~/.ntes").expanduser(),
    "editor": os.environ.get("EDITOR", "vim"),
}
NOTES_CONFIG = (
    json.loads(NOTES_CONFIG_FILE.read_text())
    if NOTES_CONFIG_FILE.is_file()
    else NOTES_CONFIG_DEFAULT
)
NOTES_CONFIG["notes_dir"].mkdir(parents=True, exist_ok=True)
NOTE_PATH = NOTES_CONFIG["notes_dir"]
TODAY = date.today().isoformat()
NOW = datetime.now().isoformat()

app = typer.Typer()


def note_value(key: str) -> str:
    note_file = NOTE_PATH / key
    if not note_file.is_file():
        typer.echo(f"No value stored for {key}!")
        raise typer.Abort()
    return note_file.read_text()


@app.command(name="set")
def _set(key: str, value: str, overwrite: bool = False):
    note_file = NOTE_PATH / key
    if note_file.exists() and not (overwrite or typer.confirm(f"Replace existing note for {key}.")):
        raise typer.Abort()
    note_file.write_text(value)


@app.command()
def edit(key: str, using: str = NOTES_CONFIG["editor"]):
    call((using, NOTE_PATH / key))


@app.command()
def more(key: str, value: str, sep: str = "\n"):
    note_file = NOTE_PATH / key
    if not note_file.exists():
        note_file.write_text(value)
    else:
        with note_file.open("a") as note_file:
            note_file.write(sep)
            note_file.write(value)


@app.command()
def that(value: str):
    more(TODAY, value)


@app.command()
def book(using: str = NOTES_CONFIG["editor"]):
    edit(TODAY, using=using)


@app.command()
def for_today():
    get(TODAY)


@app.command()
def get(key: str):
    typer.echo(note_value(key))


@app.command()
def todo(task: str, key: str = "TODOS"):
    more(key, f"- [ ] {task}")


@app.command()
def done(task: str, key: str = "TODOS"):
    _set(
        key,
        note_value(key).replace(f"- [ ] {task}", f"- [x] {task} (Completed: {NOW})", 1),
        overwrite=True,
    )


@app.command()
def clear_done(key: str = "TODOS"):
    _set(
        key,
        "\n".join(
            line for line in note_value(key).splitlines() if line and not line.startswith("- [x]")
        ),
        overwrite=True,
    )


@app.command()
def todos(key: str = "TODOS"):
    get(key)


@app.command()
def run(key: str):
    call(note_value(key), shell=True)
    note_file = NOTE_PATH / key
    os.chmod(note_file, os.stat(note_file).st_mode | stat.S_IEXEC)


@app.command()
def recent(amount: int = 10, lines: int = 3):
    for note_file in sorted(NOTE_PATH.glob("*"), key=os.path.getctime, reverse=True)[:amount]:
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
    for note_file in sorted(NOTE_PATH.glob("*"), key=os.path.getctime, reverse=True):
        if os.access(note_file, os.X_OK):
            typer.secho(note_file.name, fg=typer.colors.GREEN)
        else:
            typer.echo(note_file.name)


if __name__ == "__main__":
    app()
