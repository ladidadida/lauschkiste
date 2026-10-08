"""Downloads the audio files of one book into a folder. Runs as a process of its own, with the lowest priority.

    python -m lauschkiste_plugin_audiobookshelf.downloader SERVER BOOK DEST RATE_FILE

The API key comes in the environment variable ``ABS_API_KEY``. ``RATE_FILE`` holds the speed limit in
kB/s (empty or 0: none, -1: wait) and is read again while downloading. Progress is written to ``DEST/status.json``;
files are renamed into place when complete, ``meta.json`` marks the book as complete.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

CHUNK = 64 * 1024
TIMEOUT = (10, 60)
STATUS_EVERY_SEC = 1.0


class DownloadError(Exception):
    pass


def lower_priority() -> None:
    try:
        os.nice(19)
    except OSError:
        pass
    try:
        subprocess.run(['ionice', '-c', '3', '-p', str(os.getpid())], check=False, capture_output=True)
    except OSError:
        pass


def read_rate(path: Path) -> float:
    try:
        return float(path.read_text().strip() or 0)
    except (OSError, ValueError):
        return 0.0


def write_json(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(data))
    os.replace(tmp, path)


class Download:
    def __init__(self, server: str, key: str, book: str, dest: Path, rate_file: Path):
        self.base = server.rstrip('/')
        self.book, self.dest, self.rate_file = book, dest, rate_file
        self.session = requests.Session()
        self.session.headers['Authorization'] = f'Bearer {key}'
        self.done = 0
        self.total = 0
        self._status_at = 0.0

    def status(self, state: str, **extra) -> None:
        write_json(self.dest / 'status.json', {'state': state, 'done': self.done, 'total': self.total, **extra})
        self._status_at = time.monotonic()

    def item(self) -> Dict[str, Any]:
        response = self.session.get(f'{self.base}/api/items/{self.book}', timeout=TIMEOUT)
        if response.status_code in (401, 403):
            raise DownloadError('the server refused the API key')
        if response.status_code == 404:
            raise DownloadError('the book does not exist on the server')
        response.raise_for_status()
        return response.json()

    def run(self) -> None:
        self.dest.mkdir(parents=True, exist_ok=True)
        item = self.item()
        files: List[Dict[str, Any]] = sorted((item.get('media') or {}).get('audioFiles') or [],
                                             key=lambda f: f.get('index', 0))
        if not files:
            raise DownloadError('the book has no audio files')
        names = [f"{number:03d}_{audio['ino']}{audio['metadata'].get('ext') or ''}"
                 for number, audio in enumerate(files, 1)]
        sizes = [int(audio['metadata']['size']) for audio in files]
        self.total = sum(sizes)
        self.status('downloading')
        for audio, name, size in zip(files, names, sizes):
            target = self.dest / name
            if target.exists() and target.stat().st_size == size:
                self.done += size
                continue
            self.fetch(audio['ino'], target, size)
        write_json(self.dest / 'meta.json', {
            'book': self.book, 'title': (item.get('media') or {}).get('metadata', {}).get('title'),
            'updatedAt': item.get('updatedAt'), 'size': self.total,
            'files': [{'name': name, 'ino': audio['ino'], 'size': size, 'duration': audio.get('duration')}
                      for audio, name, size in zip(files, names, sizes)]})
        self.status('done')

    def fetch(self, ino: str, target: Path, size: int) -> None:
        part = target.with_name(target.name + '.part')
        have = part.stat().st_size if part.exists() else 0
        if have > size:
            part.unlink()
            have = 0
        self.done += have
        if have < size:
            headers = {'Range': f'bytes={have}-'} if have else {}
            url = f'{self.base}/api/items/{self.book}/file/{ino}/download'
            with self.session.get(url, headers=headers, stream=True, timeout=TIMEOUT) as response:
                if response.status_code == 416:
                    part.unlink()
                    raise DownloadError('the partial file does not fit the server copy, try again')
                response.raise_for_status()
                if have and response.status_code != 206:
                    part.unlink()
                    raise DownloadError('the server does not continue partial downloads, try again')
                with open(part, 'ab') as stream:
                    self.copy(response, stream)
        if part.stat().st_size != size:
            part.unlink()
            raise DownloadError(f'{target.name} has the wrong size')
        os.replace(part, target)

    def copy(self, response, stream) -> None:
        started, sent = time.monotonic(), 0
        rate, rate_at = 0.0, 0.0
        for chunk in response.iter_content(CHUNK):
            stream.write(chunk)
            self.done += len(chunk)
            sent += len(chunk)
            now = time.monotonic()
            if now - rate_at >= 1.0:
                rate, rate_at = read_rate(self.rate_file) * 1000, now
            while rate < 0:
                time.sleep(1.0)
                rate = read_rate(self.rate_file) * 1000
                started, sent = time.monotonic(), 0
            if rate:
                ahead = sent / rate - (now - started)
                if ahead > 0:
                    time.sleep(min(ahead, 2.0))
            if now - self._status_at >= STATUS_EVERY_SEC:
                self.status('downloading')


def main(argv: List[str]) -> int:
    server, book, dest, rate_file = argv[1], argv[2], Path(argv[3]), Path(argv[4])
    lower_priority()
    download = Download(server, os.environ.get('ABS_API_KEY', ''), book, dest, rate_file)
    try:
        download.run()
    except (DownloadError, requests.RequestException, OSError, KeyError) as error:
        dest.mkdir(parents=True, exist_ok=True)
        download.status('error', error=f'{error.__class__.__name__}: {error}' if not isinstance(error, DownloadError)
                        else str(error))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
