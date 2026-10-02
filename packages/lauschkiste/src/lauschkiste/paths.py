"""Where Lauschkiste keeps its data (``LAUSCHKISTE_HOME``) and its packaged resources.

All runtime data lives below one directory::

    $LAUSCHKISTE_HOME/settings/      configuration, card database, library index, status files
    $LAUSCHKISTE_HOME/library/       the library: music/, audiobooks/
    $LAUSCHKISTE_HOME/logs/  cache/  playlists/

Relative paths in the configuration are resolved against ``LAUSCHKISTE_HOME``.
"""

import os
from importlib import resources
from pathlib import Path
from typing import Optional, Union

ENV_PREFIX = 'LAUSCHKISTE_'
HOME_ENV = ENV_PREFIX + 'HOME'
CONFIG_FILE = 'lauschkiste.yaml'
LIBRARY_DIR = 'library'
MUSIC_DIR = 'music'
AUDIOBOOKS_DIR = 'audiobooks'

_home: Optional[Path] = None


def env_name(name: str) -> str:
    return ENV_PREFIX + name


def getenv(name: str) -> Optional[str]:
    return os.environ.get(env_name(name)) or None


def default_home() -> Path:
    xdg_data_home = os.environ.get('XDG_DATA_HOME')
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / '.local' / 'share'
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


def resolve(value: Union[str, Path]) -> Path:
    """A configured path: absolute or ``~`` as given, relative ones below the home."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return home() / path


def library_dir(configured: Union[str, Path, None] = None) -> Path:
    """The library (``library.path``, by default ``library`` in the home)."""
    return resolve(configured or LIBRARY_DIR)


def settings_dir() -> Path:
    return home() / 'settings'


def config_file() -> Path:
    return settings_dir() / CONFIG_FILE


def resource(*parts: str) -> Path:
    """A file shipped with the package (default settings, sounds, service templates)."""
    return Path(str(resources.files('lauschkiste').joinpath('resources', *parts)))
