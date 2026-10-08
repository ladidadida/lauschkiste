import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

pytest.importorskip('lauschkiste_plugin_audiobookshelf', reason="the audiobookshelf plugin package is not installed")

from lauschkiste.contract import OperationError
from lauschkiste_plugin_audiobookshelf.source import AudiobookshelfSource

KEY = 'secret-key'
BOOK = {
    'id': 'book1', 'mediaType': 'book',
    'media': {'metadata': {'title': 'Bullerbü'}, 'duration': 300.0, 'numAudioFiles': 3,
              'audioFiles': [{'ino': '30', 'index': 3, 'duration': 100.0}, {'ino': '10', 'index': 1, 'duration': 70.0},
                             {'ino': '20', 'index': 2, 'duration': 130.0}]},
}


class FakeServer(BaseHTTPRequestHandler):
    progress = {}
    requests = []

    def log_message(self, *args):
        pass

    def reply(self, status, body=None):
        data = json.dumps(body).encode() if body is not None else b''
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_any(self):
        length = int(self.headers.get('Content-Length') or 0)
        body = json.loads(self.rfile.read(length)) if length else None
        type(self).requests.append((self.command, self.path, body))
        if self.headers.get('Authorization') != f'Bearer {KEY}':
            return self.reply(401, {})
        path = self.path.split('?')[0]
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
    FakeServer.progress, FakeServer.requests = {}, []
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
