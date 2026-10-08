import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

pytest.importorskip('lauschkiste_plugin_audiobookshelf', reason="the audiobookshelf plugin package is not installed")

from lauschkiste.contract import OperationError
from lauschkiste_plugin_audiobookshelf.downloader import Download, DownloadError
from lauschkiste_plugin_audiobookshelf.downloads import DownloadCache, DownloadManager
from lauschkiste_plugin_audiobookshelf.source import AudiobookshelfSource

KEY = 'secret-key'
CONTENT = {'10': bytes(range(256)) * 4, '20': b'B' * 3000, '30': b'C' * 500}


def audio(ino, index, duration):
    return {'ino': ino, 'index': index, 'duration': duration,
            'metadata': {'ext': '.mp3', 'size': len(CONTENT[ino]), 'filename': f'{index}.mp3'}}


BOOK = {
    'id': 'book1', 'mediaType': 'book', 'updatedAt': 1000,
    'media': {'metadata': {'title': 'Bullerbü'}, 'duration': 300.0, 'numAudioFiles': 3,
              'audioFiles': [audio('30', 3, 100.0), audio('10', 1, 70.0), audio('20', 2, 130.0)]},
}


class FakeServer(BaseHTTPRequestHandler):
    progress = {}
    requests = []
    ranges = []

    def log_message(self, *args):
        pass

    def reply(self, status, body=None):
        data = json.dumps(body).encode() if body is not None else b''
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, content):
        start = 0
        header = self.headers.get('Range')
        if header:
            start = int(header.split('=')[1].rstrip('-'))
        type(self).ranges.append(header)
        body = content[start:]
        self.send_response(206 if header else 200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_any(self):
        length = int(self.headers.get('Content-Length') or 0)
        body = json.loads(self.rfile.read(length)) if length else None
        type(self).requests.append((self.command, self.path, body))
        if self.headers.get('Authorization') != f'Bearer {KEY}':
            return self.reply(401, {})
        path = self.path.split('?')[0]
        parts = path.split('/')
        if len(parts) == 7 and parts[1:4] == ['api', 'items', 'book1'] and parts[4] == 'file':
            return self.send_file(CONTENT[parts[5]])
        if path == '/api/libraries':
            return self.reply(200, {'libraries': [{'id': 'lib1', 'mediaType': 'book'},
                                                  {'id': 'pod', 'mediaType': 'podcast'}]})
        if path == '/api/libraries/lib1/items':
            return self.reply(200, {'results': [BOOK]})
        if path == '/api/items/book1':
            return self.reply(200, BOOK)
        if path == '/api/me':
            return self.reply(200, {'mediaProgress': list(type(self).progress.values())})
        if path == '/api/me/progress/book1':
            if self.command == 'PATCH':
                type(self).progress['book1'] = {'libraryItemId': 'book1', 'currentTime': body['currentTime'],
                                                'isFinished': body['isFinished']}
                return self.reply(200, {})
            entry = type(self).progress.get('book1')
            return self.reply(200 if entry else 404, entry)
        self.reply(404, {})

    do_GET = do_PATCH = handle_any


@pytest.fixture
def server():
    FakeServer.progress, FakeServer.requests, FakeServer.ranges = {}, [], []
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), FakeServer)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{httpd.server_port}'
    httpd.shutdown()


@pytest.fixture
def source(server):
    source = AudiobookshelfSource()
    source.configure(server, KEY, 10)
    return source


def test_lists_the_books_of_book_libraries_with_progress(source):
    FakeServer.progress['book1'] = {'libraryItemId': 'book1', 'currentTime': 90.0, 'isFinished': False}
    assert source.list_books() == [{
        'book': 'book1', 'title': 'Bullerbü', 'chapters': 3, 'duration': 300.0, 'chapter': 1, 'elapsed': 20.0,
        'listened': 90.0, 'finished': False,
        'cover_url': '/api/v1/audiobookshelf/covers/book1'}]
    assert not any('pod' in path for _, path, _ in FakeServer.requests)


def test_unconfigured_lists_nothing_and_cannot_play():
    source = AudiobookshelfSource()
    assert source.list_books() == []
    with pytest.raises(OperationError) as error:
        source.files('book1')
    assert error.value.status == 503


def test_tracks_are_in_file_order_without_secrets(source):
    assert source.files('book1') == ['abs://book1/10', 'abs://book1/20', 'abs://book1/30']


def test_resolver_adds_the_key_as_header_only(source, server):
    url, headers = source.resolve('abs://book1/20')
    assert url == f'{server}/api/items/book1/file/20/download'
    assert headers == {'Authorization': f'Bearer {KEY}'}
    assert KEY not in url


def test_position_is_read_from_and_written_to_the_server(source):
    position = source.position('book1')
    assert position.load() == {}

    position.save({'file': 'abs://book1/20', 'elapsed': 15.0, 'finished': False})
    assert FakeServer.progress['book1']['currentTime'] == 85.0
    assert position.load() == {'file': 'abs://book1/20', 'elapsed': 15.0, 'finished': False}

    position.save({'finished': True})
    assert FakeServer.progress['book1'] == {'libraryItemId': 'book1', 'currentTime': 300.0, 'isFinished': True}
    assert position.load() == {'finished': True}


def test_set_finished_and_back(source):
    source.set_finished('book1', True)
    assert FakeServer.progress['book1']['isFinished'] is True
    source.set_finished('book1', False)
    assert FakeServer.progress['book1'] == {'libraryItemId': 'book1', 'currentTime': 0.0, 'isFinished': False}


def test_unknown_book(source):
    with pytest.raises(OperationError) as error:
        source.files('nope')
    assert error.value.status == 404


def test_wrong_key_is_reported(server):
    source = AudiobookshelfSource()
    source.configure(server, 'wrong', 10)
    with pytest.raises(Exception, match='refused the API key'):
        source.list_books()


# -- downloads --------------------------------------------------------------------------------

def fetch(server, directory, key=KEY):
    Download(server, key, 'book1', directory, directory.parent / 'rate').run()


def test_download_writes_all_files_and_marks_the_book_complete(server, tmp_path):
    cache = DownloadCache(tmp_path)
    fetch(server, cache.directory('book1'))
    meta = cache.complete('book1')
    assert [f['name'] for f in meta['files']] == ['001_10.mp3', '002_20.mp3', '003_30.mp3']
    assert (cache.directory('book1') / '001_10.mp3').read_bytes() == CONTENT['10']
    assert cache.status_of('book1')['state'] == 'done'
    assert cache.used_bytes() == sum(len(c) for c in CONTENT.values())
    assert not list(cache.directory('book1').glob('*.part'))


def test_a_partial_file_is_continued_with_a_range_request(server, tmp_path):
    cache = DownloadCache(tmp_path)
    directory = cache.directory('book1')
    directory.mkdir(parents=True)
    (directory / '002_20.mp3.part').write_bytes(CONTENT['20'][:1000])
    fetch(server, directory)
    assert (directory / '002_20.mp3').read_bytes() == CONTENT['20']
    assert 'bytes=1000-' in FakeServer.ranges


def test_download_with_a_wrong_key_reports_an_error(server, tmp_path):
    with pytest.raises(DownloadError, match='refused'):
        fetch(server, tmp_path / 'b', key='wrong')


def test_the_rate_file_slows_the_download_down(server, tmp_path):
    cache = DownloadCache(tmp_path)
    cache.set_rate(100)
    directory = cache.directory('book1')
    directory.parent.mkdir(exist_ok=True)
    Download(server, KEY, 'book1', directory, cache.rate_file).run()
    assert cache.complete('book1')


def test_manager_downloads_in_a_process_and_the_source_then_plays_the_files(server, tmp_path):
    source = AudiobookshelfSource()
    source.configure(server, KEY, 10)
    source.cache = DownloadCache(tmp_path)
    manager = DownloadManager(source.cache, source.credentials)
    manager.start('book1')
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and not source.cache.complete('book1'):
        time.sleep(0.1)
    assert source.cache.complete('book1')
    assert [s['state'] for s in manager.states()] == ['done']

    files = source.files('book1')
    assert files == [str(tmp_path / 'book1' / name) for name in ('001_10.mp3', '002_20.mp3', '003_30.mp3')]
    FakeServer.progress['book1'] = {'libraryItemId': 'book1', 'currentTime': 90.0, 'isFinished': False}
    assert source.position('book1').load() == {'file': files[1], 'elapsed': 20.0, 'finished': False}

    source.prefer_downloaded = False
    assert source.files('book1')[0].startswith('abs://')
    manager.remove('book1')
    assert source.cache.books() == []
    manager.close()
