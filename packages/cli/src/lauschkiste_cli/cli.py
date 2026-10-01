import os
from pathlib import Path

from dotenv import dotenv_values, find_dotenv


def load_env() -> None:
    """``LAUSCHKISTE_*`` defaults from the nearest ``.env`` above this file (a source checkout's).

    Relative paths in it are relative to the ``.env`` file. The environment wins over the file.
    Runs at import: typer reads ``envvar`` options from os.environ.
    """
    path = find_dotenv()
    if not path:
        return
    for key, value in dotenv_values(path).items():
        if key.startswith(('LAUSCHKISTE_', 'JUKEBOX_')) and key not in os.environ and value is not None:
            if key.split('_', 1)[1] in ('HOME', 'WEBAPP_DIR', 'CONF', 'LOGGER_CONF'):
                value = str(Path(path).parent / Path(value).expanduser())
            os.environ[key] = value


load_env()

from typing import Optional  # noqa: E402

import typer  # noqa: E402

import lauschkiste.paths  # noqa: E402
from lauschkiste_cli import debug, plugin  # noqa: E402
from lauschkiste_cli.setup import setup  # noqa: E402
from lauschkiste_cli.update import update  # noqa: E402
from lauschkiste_cli.run import run  # noqa: E402

app = typer.Typer(name="jukebox", help="Jukebox CLI.")


@app.callback()
def main(home: Optional[Path] = typer.Option(
        None, "--home", envvar=lauschkiste.paths.env_names("HOME"),
        help="Directory with all data (settings, music, logs). "
             "Default: $XDG_DATA_HOME/lauschkiste (~/.local/share/lauschkiste).")) -> None:
    lauschkiste.paths.set_home(home)


@app.command(name="home")
def show_home() -> None:
    """Print the home directory and the configuration file in use."""
    typer.echo(f"home:   {lauschkiste.paths.home()}")
    typer.echo(f"config: {lauschkiste.paths.config_file()}")


app.command(name="run")(run)
app.command(name="setup")(setup)
app.command(name="update")(update)
app.add_typer(debug.app, name="debug")
app.add_typer(plugin.app, name="plugin")
