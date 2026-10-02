"""The library: file management, index, metadata and cover art."""

import lauschkiste.cfghandler
import lauschkiste.paths
from lauschkiste.library.files import (
    AUDIO_EXTENSIONS, MAX_UPLOAD_SIZE, LibraryError, MusicLibrary, resolve_library_path,
)

__all__ = ['AUDIO_EXTENSIONS', 'MAX_UPLOAD_SIZE', 'LibraryError', 'MusicLibrary', 'resolve_library_path', 'root']


def root() -> str:
    """The library directory, from ``library.path``."""
    configured = lauschkiste.cfghandler.get_handler('lauschkiste').getn('library', 'path', default=None)
    return str(lauschkiste.paths.library_dir(configured))
