"""`lauschctl config ...`: read and change single settings in the configuration file."""

from io import StringIO
from pathlib import Path
from typing import Optional

import typer
from ruamel.yaml import YAML, YAMLError

import lauschkiste.cfghandler
from lauschkiste_cli.plugin import ConfOption, _config

app = typer.Typer(help="Read and change single settings.", no_args_is_help=True)

_MISSING = object()


def _keys(key: str) -> list:
    keys = key.split('.')
    if not all(keys):
        raise typer.BadParameter(f"'{key}' is not a setting name like library.path")
    return keys


def _dump(value) -> str:
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if not isinstance(value, (dict, list)):
        return str(value)
    out = StringIO()
    yaml = YAML(typ='safe')
    yaml.default_flow_style = None
    yaml.dump(_plain(value), out)
    return out.getvalue().rstrip()


def _plain(value):
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


@app.command('get')
def get_setting(key: str = typer.Argument(..., help="e.g. library.path"),
                conf: Optional[Path] = ConfOption) -> None:
    """Print a setting (a section is printed as YAML)."""
    cfg, _ = _config(conf)
    value = cfg.getn(*_keys(key), default=_MISSING)
    if value is _MISSING:
        typer.echo(f"{key} is not set in the configuration file", err=True)
        raise typer.Exit(1)
    typer.echo(_dump(value))


@app.command('set')
def set_setting(key: str = typer.Argument(..., help="e.g. library.path"),
                value: str = typer.Argument(..., help="a YAML value: text, number, true/false, [a, b]"),
                conf: Optional[Path] = ConfOption) -> None:
    """Change a setting. Takes effect when Lauschkiste is restarted."""
    keys = _keys(key)
    try:
        parsed = YAML(typ='safe').load(value)
    except YAMLError:
        parsed = value
    cfg, path = _config(conf)
    if isinstance(cfg.getn(*keys, default=None), dict):
        typer.echo(f"{key} is a section; set one of its settings, e.g. {key}.<name>", err=True)
        raise typer.Exit(1)
    cfg.setn(*keys, value=parsed)
    lauschkiste.cfghandler.write_yaml(cfg, str(path))
    typer.echo(f"{key}: {_dump(parsed)}")
