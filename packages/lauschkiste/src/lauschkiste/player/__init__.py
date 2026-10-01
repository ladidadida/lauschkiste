import os
import re
import logging
import lauschkiste.cfghandler
import lauschkiste.paths
from typing import Optional


logger = logging.getLogger('lauschkiste.player')
cfg = lauschkiste.cfghandler.get_handler('lauschkiste')


def _get_music_library_path(conf_file):
    """Parse the music directory from the mpd.conf file"""
    pattern = re.compile(r'^\s*music_directory\s*"(.*)"', re.I)
    directory = None
    with open(conf_file, 'r') as f:
        for line in f:
            res = pattern.match(line)
            if res:
                directory = res.group(1)
                break
        else:
            logger.error(f"Could not find music library path in {conf_file}")
    logger.debug(f"MPD music lib path = {directory}; from {conf_file}")
    return directory


class MusicLibPath:
    """Determine the music library directory.

    Primarily from `player.music_library_path` config (backend-agnostic). Falls back to parsing
    `music_directory` out of mpd.conf only when the mpd backend is active and no explicit path was
    configured -- keeps existing mpd installs working without a migration step.
    """
    def __init__(self):
        configured = cfg.getn('player', 'music_library_path', default=None)
        if configured is not None:
            self._music_library_path = str(lauschkiste.paths.resolve(configured))
            return
        if cfg.getn('player', 'backend', default='local_audio') != 'mpd':
            self._music_library_path = str(lauschkiste.paths.resolve('audiofolders'))
            return
        mpd_conf_file = cfg.getn('playermpd', 'mpd_conf', default='~/.config/mpd/mpd.conf')
        try:
            self._music_library_path = _get_music_library_path(os.path.expanduser(mpd_conf_file))
        except Exception as e:
            logger.error(f"Could not determine music library directory from '{mpd_conf_file}'")
            logger.error(f"Reason: {e.__class__.__name__}: {e}")

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
