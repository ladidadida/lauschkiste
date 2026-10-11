from pathlib import Path
from typing import Optional

import typer

import lauschkiste.common.paths
from lauschkiste_cli.run import run

HOME_HELP = ("Directory with all data (settings, music, logs). "
             "Default: ~/lauschkiste on a Raspberry Pi, else $XDG_DATA_HOME/lauschkiste (~/.local/share/lauschkiste).")


def main(home: Optional[Path] = typer.Option(
        None, "--home", envvar=lauschkiste.common.paths.env_name("HOME"), help=HOME_HELP)) -> None:
    lauschkiste.common.paths.set_home(home)


def show_home() -> None:
    """Print the home directory and the configuration file in use."""
    typer.echo(f"home:   {lauschkiste.common.paths.home()}")
    typer.echo(f"config: {lauschkiste.common.paths.config_file()}")


def _management_app(name: str, help_text: str) -> typer.Typer:
    from lauschkiste_cli import config, debug, plugin
    from lauschkiste_cli.setup import setup
    from lauschkiste_cli.uninstall import uninstall
    from lauschkiste_cli.update import update

    app = typer.Typer(name=name, help=help_text, no_args_is_help=True)
    app.callback()(main)
    app.command(name="home")(show_home)
    app.command(name="setup")(setup)
    app.command(name="update")(update)
    app.command(name="uninstall")(uninstall)
    app.add_typer(config.app, name="config")
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
