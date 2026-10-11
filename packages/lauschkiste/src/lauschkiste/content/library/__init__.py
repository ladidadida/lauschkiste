"""The library: file management, index, metadata and cover art."""

import lauschkiste.common.cfghandler
import lauschkiste.common.paths
from lauschkiste.content.library.files import (
    AUDIO_EXTENSIONS, MAX_UPLOAD_SIZE, LibraryError, MusicLibrary, resolve_library_path,
)

__all__ = ['AUDIO_EXTENSIONS', 'MAX_UPLOAD_SIZE', 'LibraryError', 'MusicLibrary', 'resolve_library_path', 'root']


def root() -> str:
    """The library directory, from ``library.path``."""
    configured = lauschkiste.common.cfghandler.get_handler('lauschkiste').getn('library', 'path', default=None)
    return str(lauschkiste.common.paths.library_dir(configured))
