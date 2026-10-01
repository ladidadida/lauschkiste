import json
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from starlette.testclient import TestClient

from lauschkiste.contract import CoreModule, query
from lauschkiste.api.events import EventBroker, MAX_MESSAGE_SIZE
from lauschkiste.api.fastapi_server import FastApiServer, create_app
from lauschkiste.library.module import Library
from lauschkiste.publishing.bus import EventBus


class FakeClient:
    def __init__(self):
        self.subscriptions = set()
        self.messages = []

    def write_message(self, message):
        self.messages.append(message)
        return None


def _make_client():
    executor = ThreadPoolExecutor(max_workers=1)
    app = create_app(EventBroker(), executor)
    client = TestClient(app)
    return client, executor


def test_broker_uses_prefix_matching_and_per_client_snapshots():
    bus = EventBus()
    broker = EventBroker(bus=bus)
    player = FakeClient()
    core = FakeClient()
    bus.publish('player.status', {'playing': True})
    bus.publish('core.version', '3.0')

    broker.register(player)
    broker.register(core)
    broker.subscribe(player, ['player'])
    broker.subscribe(core, ['core.version'])

    assert player.messages == [{
        'type': 'event',
        'topic': 'player.status',
        'data': {'playing': True},
    }]
    assert core.messages == [{
        'type': 'event',
        'topic': 'core.version',
        'data': '3.0',
    }]


def test_broker_subscribe_all_unsubscribe_and_revoke():
    bus = EventBus()
    broker = EventBroker(bus=bus)
    client = FakeClient()
    bus.register(broker.publish)
    broker.register(client)
    broker.subscribe(client, [''])

    bus.publish('volume.level', 12)
    bus.publish('volume.level', None)
    broker.unsubscribe(client, [''])
    bus.publish('volume.level', 13)

    assert client.messages == [
        {'type': 'event', 'topic': 'volume.level', 'data': 12},
        {'type': 'revoke', 'topic': 'volume.level'},
    ]
    # The cache updates on every publish() regardless of subscribers; the client just didn't get
    # this last one delivered since it unsubscribed first.
    assert bus.cache_snapshot()['volume.level'] == 13


class RecordingSource:
    def __init__(self):
        self.refreshed = 0

    def describe(self):
        return {'id': 'recording', 'label': 'Recording', 'views': []}

    def list_items(self, content_types):
        return []

    def list_songs(self, albumartist, album, content_uri):
        return []

    def get_song(self, song_url):
        return None

    def cover(self, song_url):
        return None

    def refresh(self):
        self.refreshed += 1


@pytest.fixture
def library_client(api_client, tmp_path):
    source = RecordingSource()

    class LibraryWithSource(Library):
        def start(self, ctx):
            super().start(ctx)
            self.sources.register('recording', source)

    music = tmp_path / 'music'
    music.mkdir()
    config = {'library': {'path': str(music), 'index': str(tmp_path / 'index.sqlite'),
                          'cover_cache': str(tmp_path / 'covers'), 'scan_on_startup': False}}
    with api_client([LibraryWithSource], config) as client:
        yield client, music, source


def test_health():
    client, executor = _make_client()
    try:
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        assert response.json() == {'status': 'ok'}
    finally:
        executor.shutdown(wait=True, cancel_futures=True)


def test_events_subscribe_receives_snapshot_and_rejects_bad_command():
    bus = EventBus()
    bus.publish('core.version', 'test-version')
    broker = EventBroker(bus=bus)
    executor = ThreadPoolExecutor(max_workers=1)
    app = create_app(broker, executor)
    client = TestClient(app)
    try:
        with client.websocket_connect('/api/v1/events') as websocket:
            websocket.send_json({'type': 'subscribe', 'topics': ['core']})
            message = websocket.receive_json()
            assert message == {
                'type': 'event',
                'topic': 'core.version',
                'data': 'test-version',
            }
    finally:
        executor.shutdown(wait=True, cancel_futures=True)


def test_events_websocket_rejects_cross_origin_handshake():
    executor = ThreadPoolExecutor(max_workers=1)
    app = create_app(EventBroker(), executor)
    client = TestClient(app)
    try:
        with pytest.raises(Exception):  # noqa: B017 -- starlette.testclient raises WebSocketDisconnect
            with client.websocket_connect(
                '/api/v1/events',
                headers={'Origin': 'http://not-the-jukebox.invalid'},
            ):
                pass
    finally:
        executor.shutdown(wait=True, cancel_futures=True)


def test_events_websocket_allows_same_origin_and_no_origin_header():
    executor = ThreadPoolExecutor(max_workers=1)
    app = create_app(EventBroker(), executor)
    client = TestClient(app)
    try:
        with client.websocket_connect('/api/v1/events', headers={'Origin': 'http://testserver'}):
            pass
        with client.websocket_connect('/api/v1/events'):
            pass
    finally:
        executor.shutdown(wait=True, cancel_futures=True)


def test_library_upload_create_delete_and_refresh(library_client):
    client, library_directory, source = library_client

    folder_response = client.post(
        '/api/v1/library/folders',
        headers={'Content-Type': 'application/json'},
        content=json.dumps({'parent': '.', 'name': 'Album'}),
    )
    assert folder_response.status_code == 201
    assert folder_response.json() == {'path': 'Album'}

    upload_response = client.put(
        '/api/v1/library/files',
        params={'folder': 'Album', 'name': 'track.mp3'},
        headers={'Content-Type': 'audio/mpeg'},
        content=b'audio data',
    )
    assert upload_response.status_code == 201
    assert upload_response.json() == {'path': 'Album/track.mp3', 'size': 10}
    assert (library_directory / 'Album' / 'track.mp3').read_bytes() == b'audio data'

    list_response = client.get('/api/v1/library/entries', params={'folder': 'Album'})
    assert list_response.status_code == 200
    assert list_response.json() == {
        'entries': [{'name': 'track.mp3', 'relpath': 'Album/track.mp3', 'type': 'file'}],
    }

    duplicate_response = client.put(
        '/api/v1/library/files',
        params={'folder': 'Album', 'name': 'track.mp3'},
        content=b'replacement',
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()['error']['code'] == 'duplicate_name'

    refresh_response = client.post('/api/v1/library/refresh', content=b'')
    assert refresh_response.status_code == 200
    assert refresh_response.json() == {'scanning': True}
    assert source.refreshed == 1

    delete_response = client.request(
        'DELETE',
        '/api/v1/library/entries',
        headers={'Content-Type': 'application/json'},
        content=json.dumps({'paths': ['Album']}),
    )
    assert delete_response.status_code == 200
    assert delete_response.json() == {'deleted': ['Album']}
    assert not (library_directory / 'Album').exists()


def test_library_endpoints_reject_invalid_types_and_paths(library_client):
    client, _library_directory, _source = library_client

    unsupported = client.put(
        '/api/v1/library/files',
        params={'folder': '.', 'name': 'archive.zip'},
        content=b'archive',
    )
    assert unsupported.status_code == 415
    assert unsupported.json()['error']['code'] == 'unsupported_file_type'

    traversal = client.put(
        '/api/v1/library/files',
        params={'folder': '..', 'name': 'track.mp3'},
        content=b'audio',
    )
    assert traversal.status_code == 400
    assert traversal.json()['error']['code'] == 'invalid_path'

    delete_root = client.request(
        'DELETE',
        '/api/v1/library/entries',
        headers={'Content-Type': 'application/json'},
        content=json.dumps({'paths': ['.']}),
    )
    assert delete_root.status_code == 400
    assert delete_root.json()['error']['code'] == 'invalid_path'


def test_library_folder_create_rejects_oversized_body(library_client):
    client, _library_directory, _source = library_client

    response = client.post(
        '/api/v1/library/folders',
        headers={'Content-Type': 'application/json'},
        content=b' ' * (MAX_MESSAGE_SIZE + 1),
    )
    assert response.status_code == 413
    assert response.json()['error']['code'] == 'request_too_large'


def test_blocking_route_does_not_block_health(api_client):
    started = threading.Event()
    release = threading.Event()

    class Slow(CoreModule):
        name = 'slow'

        @query()
        def wait(self) -> str:
            started.set()
            release.wait(1)
            return 'done'

    with api_client([Slow]) as client:
        results = {}
        worker = threading.Thread(target=lambda: results.update(slow=client.get('/api/v1/slow/wait')))
        worker.start()
        assert started.wait(1)

        health = client.get('/api/v1/health')
        assert health.status_code == 200

        release.set()
        worker.join(1)
        assert results['slow'].json() == 'done'


def test_fastapi_server_thread_lifecycle_and_stable_subscription():
    port_socket = socket.socket()
    port_socket.bind(('127.0.0.1', 0))
    port = port_socket.getsockname()[1]
    port_socket.close()

    bus = EventBus()
    server = FastApiServer(bind_address='127.0.0.1', port=port, bus=bus)
    try:
        server.start_and_wait()

        import urllib.request
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/v1/health', timeout=2) as response:
            assert json.load(response) == {'status': 'ok'}

        # Published from an arbitrary (non-event-loop) thread, same as real components do.
        bus.publish('core.version', 'test-version')
        deadline = time.monotonic() + 2
        while 'core.version' not in bus.cache_snapshot() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert bus.cache_snapshot().get('core.version') == 'test-version'
    finally:
        server.terminate()

    assert not server.is_alive()
