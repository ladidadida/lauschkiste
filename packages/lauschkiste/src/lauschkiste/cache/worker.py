"""Downloads the files of one item into its folder. Runs as a process of its own, with the lowest priority.

    python -m lauschkiste.cache.worker DEST RATE_FILE

``DEST/plan.json`` (readable for the user only, removed when the worker ends) lists the files with their address,
size and request headers. ``RATE_FILE`` holds the speed limit in kB/s (empty or 0: none, -1: wait) and is read
again while downloading. Progress goes to ``DEST/status.json``; files are renamed into place when complete and
``meta.json`` marks the item as complete.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

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
    def __init__(self, dest: Path, rate_file: Path, source: str = '', item: str = ''):
        self.dest, self.rate_file = dest, rate_file
        self.source, self.item = source, item
        self.session = requests.Session()
        self.done = 0
        self.total = 0
        self._status_at = 0.0

    def status(self, state: str, **extra) -> None:
        write_json(self.dest / 'status.json', {'state': state, 'done': self.done, 'total': self.total, **extra})
        self._status_at = time.monotonic()

    def run(self) -> None:
        plan: Dict[str, Any] = json.loads((self.dest / 'plan.json').read_text())
        files = plan['files']
        if not files:
            raise DownloadError('there is nothing to download')
        self.total = sum(int(entry.get('size') or 0) for entry in files)
        self.status('downloading')
        sizes = []
        for entry in files:
            target = self.dest / entry['name']
            size = int(entry.get('size') or 0)
            if size and target.exists() and target.stat().st_size == size:
                self.done += size
            else:
                size = self.fetch(entry['url'], entry.get('headers') or {}, target, size)
            sizes.append(size)
        write_json(self.dest / 'meta.json', {
            'source': self.source, 'item': self.item, 'title': plan.get('title') or '', 'version': plan.get('version'),
            'size': sum(sizes), 'files': [{'name': entry['name'], 'size': size, 'duration': entry.get('duration')}
                                         for entry, size in zip(files, sizes)]})
        self.status('done')

    def fetch(self, url: str, headers: Dict[str, str], target: Path, size: int) -> int:
        """Download one file; returns its size. Without a known ``size`` the file is loaded from the start
        (a listed size is often wrong) and the length it ends up with counts."""
        part = target.with_name(target.name + '.part')
        if not size and part.exists():
            part.unlink()
        have = part.stat().st_size if part.exists() else 0
        if size and have > size:
            part.unlink()
            have = 0
        self.done += have
        if not size or have < size:
            request_headers = {**headers, **({'Range': f'bytes={have}-'} if have else {})}
            with self.session.get(url, headers=request_headers, stream=True, timeout=TIMEOUT) as response:
                if response.status_code in (401, 403):
                    raise DownloadError('the server refused the access')
                if response.status_code == 416:
                    part.unlink()
                    raise DownloadError('the partial file does not fit the server copy, try again')
                response.raise_for_status()
                if have and response.status_code != 206:
                    part.unlink()
                    raise DownloadError('the server does not continue partial downloads, try again')
                if not size:
                    self.total += int(response.headers.get('Content-Length') or 0)
                with open(part, 'ab') as stream:
                    self.copy(response, stream)
        if size and part.stat().st_size != size:
            part.unlink()
            raise DownloadError(f'{target.name} has the wrong size')
        final = part.stat().st_size
        if not final:
            part.unlink()
            raise DownloadError(f'{target.name} is empty')
        os.replace(part, target)
        return final

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


def main(argv) -> int:
    dest, rate_file = Path(argv[1]), Path(argv[2])
    lower_priority()
    download = Download(dest, rate_file, source=dest.parent.name, item=dest.name)
    try:
        download.run()
    except (DownloadError, requests.RequestException, OSError, KeyError, ValueError) as error:
        message = str(error) if isinstance(error, DownloadError) else f'{error.__class__.__name__}: {error}'
        download.status('error', error=message)
        return 1
    finally:
        try:
            (dest / 'plan.json').unlink()
        except OSError:
            pass
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
