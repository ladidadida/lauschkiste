from pathlib import Path
from typing import Optional

import typer

import lauschkiste.paths
from lauschkiste_cli.run import run

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
