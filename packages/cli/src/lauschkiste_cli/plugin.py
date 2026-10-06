"""`lauschctl plugin ...`: list installed plugins, enable/disable them in the configuration, install new ones."""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import typer

import lauschkiste.cfghandler
import lauschkiste.contract.plugins as plugins
import lauschkiste.paths

app = typer.Typer(help="Manage plugins.", no_args_is_help=True)

ConfOption = typer.Option(None, "-c", "--conf", envvar=lauschkiste.paths.env_name("CONF"),
                          help="Configuration file (default: $LAUSCHKISTE_HOME/settings/lauschkiste.yaml)")


def _config(conf: Optional[Path]):
    path = conf or lauschkiste.paths.config_file()
    lauschkiste.cfghandler.ensure_default_config(
        str(path), str(lauschkiste.paths.resource('default-settings', 'lauschkiste.default.yaml')))
    cfg = lauschkiste.cfghandler.ConfigHandler('plugin-cli')
    lauschkiste.cfghandler.load_yaml(cfg, str(path))
    return cfg, path


def _enabled(cfg) -> dict:
    plugins = cfg.getn('plugins', default=None)
    return plugins if isinstance(plugins, dict) else {}


def _installed():
    return plugins.installed()


def _load(ep):
    return plugins.load(ep)


def install_requirements(requirements: List[str]) -> None:
    """Install into the environment Lauschkiste runs in (uv if available, else pip)."""
    uv = shutil.which('uv')
    if uv:
        command = [uv, 'pip', 'install', '--python', sys.executable, *requirements]
    else:
        command = [sys.executable, '-m', 'pip', 'install', *requirements]
    typer.echo(f"$ {' '.join(command)}")
    subprocess.run(command, check=True)


plugin_extras = plugins.plugin_extras
missing_extras = plugins.missing_extras


def add_to_config(path: Path, names: List[str]) -> List[str]:
    """Add ``names`` to ``plugins:`` in the configuration at ``path``; returns the newly added ones."""
    cfg, _ = _config(path)
    added = [name for name in names if name not in _enabled(cfg)]
    for name in added:
        cfg.setndefault('plugins', name, value={})
    if added:
        lauschkiste.cfghandler.write_yaml(cfg, str(path))
    return added


@app.command('list')
def list_plugins(conf: Optional[Path] = ConfOption) -> None:
    """Installed plugins, whether they are enabled, and why one can't be loaded."""
    cfg, path = _config(conf)
    enabled = _enabled(cfg)
    installed = _installed()
    for name in sorted(set(installed) | set(enabled)):
        ep = installed.get(name)
        state = 'enabled ' if name in enabled else 'disabled'
        if ep is None:
            typer.echo(f"{state}  {name:24}  NOT INSTALLED")
            continue
        cls, problem = _load(ep)
        dist = f"{ep.dist.name} {ep.dist.version}" if ep.dist else ''
        summary = problem or ((cls.__doc__ or '').strip().split('\n', 1)[0])
        typer.echo(f"{state}  {name:24}  {dist:36}  {summary}")
    typer.echo(f"\n(configuration: {path})")


@app.command()
def enable(name: str, conf: Optional[Path] = ConfOption,
           with_extras: bool = typer.Option(False, "--with-extras",
                                            help="Install the dependencies the plugin declares as extras")) -> None:
    """Enable an installed plugin (takes effect on the next start)."""
    ep = _installed().get(name)
    if ep is None:
        typer.echo(f"Plugin '{name}' is not installed. Installed: {', '.join(sorted(_installed())) or 'none'}", err=True)
        raise typer.Exit(1)
    _, problem = _load(ep)
    cfg, path = _config(conf)
    reason = plugins.why_not_enable(cfg, name)
    if reason:
        typer.echo(f"Can't enable '{name}': {reason}", err=True)
        raise typer.Exit(1)
    extras = plugin_extras(name)
    if with_extras and extras:
        install_requirements(extras)
        _, problem = _load(ep)
    elif extras:
        typer.echo(f"Note: '{name}' needs {', '.join(extras)}; install it with --with-extras if it is missing.")
    if problem and not with_extras:
        typer.echo(f"Warning: '{name}' can't be loaded right now: {problem}", err=True)
    if not add_to_config(path, [name]):
        typer.echo(f"'{name}' is already enabled in {path}")
        return
    typer.echo(f"Enabled '{name}' in {path}. Restart Lauschkiste to load it.")


@app.command()
def disable(name: str, conf: Optional[Path] = ConfOption) -> None:
    """Disable a plugin (its settings are removed from the configuration)."""
    cfg, path = _config(conf)
    enabled = _enabled(cfg)
    if name not in enabled:
        typer.echo(f"'{name}' is not enabled in {path}")
        return
    del enabled[name]
    if not enabled:
        cfg['plugins'] = {}
    lauschkiste.cfghandler.write_yaml(cfg, str(path))
    typer.echo(f"Disabled '{name}' in {path}. Restart Lauschkiste to unload it.")


@app.command()
def install(spec: str, conf: Optional[Path] = ConfOption,
            enable_plugins: bool = typer.Option(False, "--enable", help="Enable the plugins the package provides")) -> None:
    """Install a plugin package (a pip requirement, wheel file, URL or directory)."""
    before = set(_installed())
    install_requirements([spec])
    new = sorted(set(_installed()) - before)
    if not new:
        typer.echo("The package provides no new plugins (or they were installed already).")
        return
    typer.echo(f"New plugins: {', '.join(new)}")
    for name in new:
        if enable_plugins:
            enable(name, conf=conf, with_extras=False)
        else:
            typer.echo(f"  enable with: lauschctl plugin enable {name}")
