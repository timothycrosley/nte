import json
from pathlib import Path
from subprocess import call

import typer

NOTES_CONFIG_FILE = Path("~/.nte_config.json").expanduser()
NOTES_CONFIG_DEFAULT = {"datafile": Path("~/.nte_data.json").expanduser()}
NOTES_CONFIG = (
    json.loads(NOTES_CONFIG_FILE.read_text())
    if NOTES_CONFIG_FILE.is_file()
    else NOTES_CONFIG_DEFAULT
)

app = typer.Typer()
data = (
    json.loads(NOTES_CONFIG["datafile"].read_text()) if NOTES_CONFIG["datafile"].is_file() else {}
)


def save():
    Path(NOTES_CONFIG["datafile"]).write_text(json.dumps(data))


def ensure_value(key: str):
    value = data.get(key, {"value": None})["value"]
    if not value:
        typer.echo(f"No value stored for {key}!")
        raise typer.Abort()
    return value


@app.command()
def set(key: str, value: str):
    existing_value = data.get(key, {"value": None})["value"]
    if existing_value and not typer.confirm(f"Replace existing value for {key}: {existing_value}."):
        raise typer.Abort()
    data[key] = {"value": value}
    save()


@app.command()
def get(key: str):
    typer.echo(ensure_value(key))


@app.command()
def run(key: str):
    call(ensure_value(key), shell=True)


if __name__ == "__main__":
    app()
