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
        if key.startswith('LAUSCHKISTE_') and key not in os.environ and value is not None:
            if key.split('_', 1)[1] in ('HOME', 'WEBAPP_DIR', 'CONF', 'LOGGER_CONF'):
                value = str(Path(path).parent / Path(value).expanduser())
            os.environ[key] = value


load_env()

from typing import Optional  # noqa: E402

import typer  # noqa: E402

import lauschkiste.paths  # noqa: E402
from lauschkiste_cli.run import run  # noqa: E402

HOME_HELP = ("Directory with all data (settings, music, logs). "
             "Default: $XDG_DATA_HOME/lauschkiste (~/.local/share/lauschkiste).")


def main(home: Optional[Path] = typer.Option(
        None, "--home", envvar=lauschkiste.paths.env_name("HOME"), help=HOME_HELP)) -> None:
    lauschkiste.paths.set_home(home)


def show_home() -> None:
    """Print the home directory and the configuration file in use."""
    typer.echo(f"home:   {lauschkiste.paths.home()}")
    typer.echo(f"config: {lauschkiste.paths.config_file()}")


def _management_app(name: str, help_text: str) -> typer.Typer:
    from lauschkiste_cli import debug, plugin
    from lauschkiste_cli.setup import setup
    from lauschkiste_cli.update import update

    app = typer.Typer(name=name, help=help_text, no_args_is_help=True)
    app.callback()(main)
    app.command(name="home")(show_home)
    app.command(name="setup")(setup)
    app.command(name="update")(update)
    app.add_typer(debug.app, name="debug")
    app.add_typer(plugin.app, name="plugin")
    return app


#: `lauschkiste`: the server
server = typer.Typer(name="lauschkiste", add_completion=False)
server.command()(run)

def __getattr__(name: str):
    """`ctl` (`lauschctl`: everything else) is built on first use, so the server doesn't import it."""
    if name == 'ctl':
        app = _management_app("lauschctl", "Manage Lauschkiste: setup, plugins, updates.")
        globals()['ctl'] = app
        return app
    raise AttributeError(name)
