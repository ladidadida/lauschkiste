"""The parts of the Audiobookshelf API the plugin uses."""

from typing import Any, Dict, List, Optional

import requests

TIMEOUT = (5, 20)


class AudiobookshelfError(Exception):
    pass


class Client:
    def __init__(self, server_url: str, api_key: str):
        self.base = server_url.rstrip('/')
        self._headers = {'Authorization': f'Bearer {api_key}'}
        self._session = requests.Session()

    @property
    def headers(self) -> Dict[str, str]:
        return dict(self._headers)

    def request(self, method: str, path: str, **kwargs) -> Optional[Any]:
        """The decoded JSON answer; None for 404."""
        try:
            response = self._session.request(method, self.base + path, headers=self._headers, timeout=TIMEOUT, **kwargs)
        except requests.RequestException as error:
            raise AudiobookshelfError(f"Audiobookshelf is not reachable: {error.__class__.__name__}") from error
        if response.status_code == 404:
            return None
        if response.status_code in (401, 403):
            raise AudiobookshelfError("Audiobookshelf refused the API key")
        if not response.ok:
            raise AudiobookshelfError(f"Audiobookshelf answered {response.status_code} for {path}")
        return response.json() if response.content else {}

    def libraries(self) -> List[Dict[str, Any]]:
        return [library for library in (self.request('GET', '/api/libraries') or {}).get('libraries', [])
                if library.get('mediaType') == 'book']

    def books(self, library: str) -> List[Dict[str, Any]]:
        return (self.request('GET', f'/api/libraries/{library}/items', params={'limit': 0, 'minified': 1}) or {}
                ).get('results', [])

    def item(self, book: str) -> Optional[Dict[str, Any]]:
        return self.request('GET', f'/api/items/{book}')

    def progress(self) -> Dict[str, Dict[str, Any]]:
        """The progress entries of this user by library item."""
        entries = (self.request('GET', '/api/me') or {}).get('mediaProgress', [])
        return {entry['libraryItemId']: entry for entry in entries if entry.get('libraryItemId')}

    def progress_of(self, book: str) -> Optional[Dict[str, Any]]:
        return self.request('GET', f'/api/me/progress/{book}')

    def save_progress(self, book: str, position: float, duration: float, finished: bool) -> None:
        self.request('PATCH', f'/api/me/progress/{book}', json={
            'currentTime': position, 'duration': duration,
            'progress': (position / duration) if duration else 0, 'isFinished': finished})

    def cover(self, book: str, width: int):
        """The cover as a streamed response, or None."""
        try:
            response = self._session.get(f'{self.base}/api/items/{book}/cover', headers=self._headers,
                                         params={'width': width}, timeout=TIMEOUT, stream=True)
        except requests.RequestException:
            return None
        return response if response.ok else None
