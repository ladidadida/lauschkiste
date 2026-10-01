"""Where Lauschkiste keeps its data (``LAUSCHKISTE_HOME``) and its packaged resources.

All runtime data lives below one directory::

    $LAUSCHKISTE_HOME/settings/      configuration, card database, library index, status files
    $LAUSCHKISTE_HOME/audiofolders/  the music library
    $LAUSCHKISTE_HOME/logs/  cache/  playlists/

Relative paths in the configuration are resolved against ``LAUSCHKISTE_HOME``. A leading ``shared/``,
also behind ``../`` (the checkout layout before the home directory existed, relative to the
repository root or to ``src/jukebox``), is dropped, so old configurations keep working.

Installations from before the renaming keep working: ``JUKEBOX_*`` environment variables, a
``jukebox`` data directory and ``settings/jukebox.yaml`` are used when the new ones don't exist.
"""

import os
from importlib import resources
from pathlib import Path
from typing import Optional, Union

ENV_PREFIX = 'LAUSCHKISTE_'
LEGACY_ENV_PREFIX = 'JUKEBOX_'
HOME_ENV = ENV_PREFIX + 'HOME'
CONFIG_FILE = 'lauschkiste.yaml'
LEGACY_CONFIG_FILE = 'jukebox.yaml'
LEGACY_PREFIX = 'shared'

_home: Optional[Path] = None


def env_names(name: str) -> list:
    """``['LAUSCHKISTE_<name>', 'JUKEBOX_<name>']``, e.g. for typer's ``envvar``."""
    return [ENV_PREFIX + name, LEGACY_ENV_PREFIX + name]


def getenv(name: str) -> Optional[str]:
    """``$LAUSCHKISTE_<name>``, else the pre-renaming ``$JUKEBOX_<name>``."""
    for key in env_names(name):
        if os.environ.get(key):
            return os.environ[key]
    return None


def default_home() -> Path:
    xdg_data_home = os.environ.get('XDG_DATA_HOME')
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / '.local' / 'share'
    if not (base / 'lauschkiste').exists() and (base / 'jukebox').is_dir():
        return base / 'jukebox'
    return base / 'lauschkiste'


def home() -> Path:
    """The home: set explicitly, else ``$LAUSCHKISTE_HOME``, else ``$XDG_DATA_HOME/lauschkiste``."""
    global _home
    if _home is None:
        configured = getenv('HOME')
        _home = Path(configured).expanduser().resolve() if configured else default_home()
    return _home


def set_home(path: Union[str, Path, None]) -> None:
    """Use ``path`` as home (None: determine it again from the environment)."""
    global _home
    _home = Path(path).expanduser().resolve() if path is not None else None


def strip_legacy_prefix(path: Path) -> Path:
    """``shared/x`` or ``../../shared/x`` -> ``x``; anything else unchanged."""
    parts = path.parts
    ups = 0
    while ups < len(parts) and parts[ups] == '..':
        ups += 1
    if ups < len(parts) and parts[ups] == LEGACY_PREFIX:
        rest = parts[ups + 1:]
        return Path(*rest) if rest else Path('.')
    return path


def resolve(value: Union[str, Path]) -> Path:
    """A configured path: absolute or ``~`` as given, relative ones below the home."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return home() / strip_legacy_prefix(path)


def settings_dir() -> Path:
    return home() / 'settings'


def config_file() -> Path:
    """``settings/lauschkiste.yaml``, or ``settings/jukebox.yaml`` of an older installation."""
    current, legacy = settings_dir() / CONFIG_FILE, settings_dir() / LEGACY_CONFIG_FILE
    return legacy if not current.exists() and legacy.exists() else current


def resource(*parts: str) -> Path:
    """A file shipped with the package (default settings, sounds, service templates)."""
    return Path(str(resources.files('lauschkiste').joinpath('resources', *parts)))
