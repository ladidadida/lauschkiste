import logging
import threading
from typing import Any, Callable, Dict, Optional


logger = logging.getLogger('lauschkiste.player')


class PlayerCoordinator:
    """Provider-neutral facade for playback and content backends."""

    def __init__(self, second_swipe_action: Optional[Callable[[], Any]] = None):
        """
        :param second_swipe_action: runs on a second swipe of the same card instead of the
            backend's own second-swipe behavior
        """
        self._backends: Dict[str, Any] = {}
        self._default_backend_name: Optional[str] = None
        self._active_backend_name: Optional[str] = None
        self._lock = threading.RLock()
        self._second_swipe_action = second_swipe_action

    def register_backend(self, name: str, backend: Any, make_active: bool = False) -> None:
        """Register a backend, selecting the first registered backend by default."""
        if not name:
            raise ValueError("Player backend name must not be empty")
        with self._lock:
            if name in self._backends:
                raise ValueError(f"Player backend '{name}' is already registered")
            self._backends[name] = backend
            if self._default_backend_name is None:
                self._default_backend_name = name
            if self._active_backend_name is None or make_active:
                self._select_backend(name)

    def set_second_swipe_action(self, action: Optional[Callable[[], Any]]) -> None:
        self._second_swipe_action = action

    def set_default_backend(self, name: str) -> None:
        """Make ``name`` the backend used for content without an explicit provider."""
        with self._lock:
            self._get_backend(name)
            self._default_backend_name = name

    @staticmethod
    def _set_backend_active(backend: Any, active: bool) -> None:
        set_active = getattr(backend, 'set_active', None)
        if callable(set_active):
            set_active(active)

    def _get_backend(self, name: str) -> Any:
        try:
            return self._backends[name]
        except KeyError:
            available = ', '.join(self._backends) or 'none'
            raise KeyError(
                f"Unknown player backend '{name}'. Available backends: {available}"
            ) from None

    def _get_active_backend(self) -> Any:
        if self._active_backend_name is None:
            raise RuntimeError("No player backend is registered")
        return self._get_backend(self._active_backend_name)

    def _get_default_backend_name(self) -> str:
        if self._default_backend_name is None:
            raise RuntimeError("No player backend is registered")
        return self._default_backend_name

    def _select_backend(self, name: str) -> Any:
        backend = self._get_backend(name)
        if self._active_backend_name == name:
            return backend
        if self._active_backend_name is not None:
            active_backend = self._get_active_backend()
            self._call_backend(active_backend, 'stop')
            self._set_backend_active(active_backend, False)
        self._active_backend_name = name
        self._set_backend_active(backend, True)
        logger.info(f"Selected player backend '{name}'")
        return backend

    def _content_backend_name(self, provider=None) -> str:
        return provider or self._get_default_backend_name()

    def _content_backend(self, provider=None) -> Any:
        return self._select_backend(self._content_backend_name(provider))

    def _call_backend(self, backend: Any, method: str, *args, **kwargs):
        func = getattr(backend, method, None)
        if not callable(func):
            backend_name = backend.__class__.__name__
            raise NotImplementedError(
                f"Player backend '{backend_name}' does not support '{method}'"
            )
        return func(*args, **kwargs)

    def _call_named(self, backend_name: str, method: str, *args, **kwargs):
        with self._lock:
            return self._call_backend(
                self._get_backend(backend_name),
                method,
                *args,
                **kwargs,
            )

    def _call_default(self, method: str, *args, **kwargs):
        return self._call_named(
            self._get_default_backend_name(),
            method,
            *args,
            **kwargs,
        )

    def _call_active(self, method: str, *args, **kwargs):
        with self._lock:
            return self._call_backend(self._get_active_backend(), method, *args, **kwargs)

    def list_backends(self):
        with self._lock:
            return list(self._backends)

    def get_active_backend(self):
        with self._lock:
            return self._active_backend_name

    def get_default_backend(self):
        with self._lock:
            return self._default_backend_name

    def select_backend(self, name: str):
        """Stop the current backend and select another registered backend."""
        with self._lock:
            self._select_backend(name)
            return name

    def get_player_type_and_version(self):
        return self._call_active('get_player_type_and_version')

    def update(self):
        return self._call_default('update')

    def update_wait(self):
        return self._call_default('update_wait')

    def play(self):
        return self._call_active('play')

    def stop(self):
        return self._call_active('stop')

    def pause(self, state: int = 1):
        return self._call_active('pause', state)

    def prev(self):
        return self._call_active('prev')

    def next(self):
        return self._call_active('next')

    def seek(self, new_time):
        return self._call_active('seek', new_time)

    def rewind(self):
        return self._call_active('rewind')

    def replay(self):
        return self._call_active('replay')

    def toggle(self):
        return self._call_active('toggle')

    def replay_if_stopped(self):
        return self._call_active('replay_if_stopped')

    def shuffle(self, option='toggle'):
        return self._call_active('shuffle', option)

    def repeat(self, option='toggle'):
        return self._call_active('repeat', option)

    def get_current_song(self, param):
        return self._call_active('get_current_song', param)

    def map_filename_to_playlist_pos(self, filename):
        return self._call_active('map_filename_to_playlist_pos', filename)

    def remove(self):
        return self._call_active('remove')

    def move(self):
        return self._call_active('move')

    def play_single(self, song_url, provider=None):
        with self._lock:
            backend = self._content_backend(provider)
            return self._call_backend(backend, 'play_single', song_url)

    def resume(self):
        return self._call_active('resume')

    def play_card(self, folder: str, recursive: bool = False):
        with self._lock:
            backend = self._content_backend()
            if self._call_backend(backend, 'is_second_swipe', folder):
                if self._second_swipe_action is not None:
                    return self._second_swipe_action()
                return self._call_backend(backend, 'play_second_swipe')
            return self._call_backend(backend, 'play_folder', folder, recursive)

    def play_folder(self, folder: str, recursive: bool = False) -> None:
        with self._lock:
            backend = self._content_backend()
            return self._call_backend(backend, 'play_folder', folder, recursive)

    def play_files(self, paths, start=0, position=0.0):
        """Play a list of songs (paths below the library, absolute or relative)."""
        with self._lock:
            backend = self._content_backend()
            return self._call_backend(backend, 'play_files', list(paths), start, position)

    def play_album(
            self,
            albumartist: str,
            album: str,
            content_uri=None,
            provider=None):
        with self._lock:
            backend = self._content_backend(provider)
            args = (albumartist, album, content_uri) if content_uri else (albumartist, album)
            return self._call_backend(backend, 'play_album', *args)

    def queue_load(self, folder):
        return self._call_default('queue_load', folder)

    def playerstatus(self):
        return self._call_active('playerstatus')

    def playlistinfo(self):
        return self._call_active('playlistinfo')

    def get_volume(self):
        return self._call_active('get_volume')

    def set_volume(self, volume):
        return self._call_active('set_volume', volume)

    def exit(self):
        with self._lock:
            return [
                self._call_backend(backend, 'exit')
                for backend in reversed(list(self._backends.values()))
            ]
