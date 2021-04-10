import typer
import json
from pathlib import Path

NOTES_CONFIG_FILE = Path("~/.nte_config.json").expanduser()
NOTES_CONFIG_DEFAULT = {"datafile": Path("~/.nte_data.json").expanduser()}
NOTES_CONFIG = json.loads(NOTES_CONFIG_FILE.read_text()) if NOTES_CONFIG_FILE.is_file() else NOTES_CONFIG_DEFAULT

app = typer.Typer()
data = json.loads(NOTES_CONFIG["datafile"].read_text()) if NOTES_CONFIG["datafile"].is_file() else {}


def save():
    Path(NOTES_CONFIG["datafile"]).write_text(json.dumps(data))


@app.command()
def set(key: str, value: str):
    existing_value = data.get(key, {"value": None})["value"]
    if existing_value and not typer.confirm(f"Replace existing value for {key}: {existing_value}."):
        raise typer.Abort()
    data[key] = {"value": value}
    save()


@app.command()
def get(key: str):
    value = data.get(key, {"value": None})["value"]
    if not value:
        typer.echo(f"No value stored for {key}!")
        return
    typer.echo(value)




if __name__ == "__main__":
    app()
