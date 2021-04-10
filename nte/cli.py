import json
from pathlib import Path
from subprocess import call

import typer

NOTES_CONFIG_FILE = Path("~/.nte_config.json").expanduser()
NOTES_CONFIG_DEFAULT = {"notes_dir": Path("~/.ntes").expanduser()}
NOTES_CONFIG = (
    json.loads(NOTES_CONFIG_FILE.read_text())
    if NOTES_CONFIG_FILE.is_file()
    else NOTES_CONFIG_DEFAULT
)
NOTES_CONFIG["notes_dir"].mkdir(parents=True, exist_ok=True)
NOTE_PATH = NOTES_CONFIG["notes_dir"]

app = typer.Typer()

def save():
    Path(NOTES_CONFIG["datafile"]).write_text(json.dumps(data))


def note_value(key: str) -> str:
    note_file = NOTE_PATH / key
    if not note_file.is_file():
        typer.echo(f"No value stored for {key}!")
        raise typer.Abort()
    return note_file.read_text()


@app.command(name="set")
def _set(key: str, value: str, overwrite: bool=False):
    note_file = NOTE_PATH / key
    if note_file.exists() and not (overwrite or typer.confirm(f"Replace existing note for {key}.")):
        raise typer.Abort()
    note_file.write_text(value)


@app.command()
def get(key: str):
    typer.echo(note_value(key))


@app.command()
def run(key: str):
    call(note_value(key), shell=True)


if __name__ == "__main__":
    app()
