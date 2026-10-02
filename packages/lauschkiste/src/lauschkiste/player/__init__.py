import logging
import lauschkiste.cfghandler
import lauschkiste.paths
from typing import Optional


logger = logging.getLogger('lauschkiste.player')
cfg = lauschkiste.cfghandler.get_handler('lauschkiste')


class MusicLibPath:
    """The music library directory: `player.music_library_path`, by default `audiofolders`."""
    def __init__(self):
        configured = cfg.getn('player', 'music_library_path', default='audiofolders')
        self._music_library_path = str(lauschkiste.paths.resolve(configured))

    @property
    def music_library_path(self):
        return self._music_library_path


# ---------------------------------------------------------------------------


_MUSIC_LIBRARY_PATH: Optional[MusicLibPath] = None


def get_music_library_path():
    """Get the music library path"""
    global _MUSIC_LIBRARY_PATH
    if _MUSIC_LIBRARY_PATH is None:
        _MUSIC_LIBRARY_PATH = MusicLibPath()
    return _MUSIC_LIBRARY_PATH.music_library_path
