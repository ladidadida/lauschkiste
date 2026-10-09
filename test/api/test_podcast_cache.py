import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock

import pytest

import lauschkiste.cache
import lauschkiste.podcasts
import lauschkiste.resume
from lauschkiste.podcasts import parse_feed

AUDIO = {'/1.mp3': b'one' * 2000, '/2.mp3': b'two' * 1500}


class Audio(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        body = AUDIO[self.path]
        self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def audio_server():
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Audio)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{httpd.server_port}'
    httpd.shutdown()


def rss(server):
    return f'''<?xml version="1.0"?><rss version="2.0"><channel><title>Kakadu</title>
<item><title>Older</title><guid>ep-1</guid><pubDate>Mon, 01 Sep 2026 07:00:00 +0200</pubDate>
<enclosure url="{server}/1.mp3" type="audio/mpeg" length="1"/></item>
<item><title>Newer</title><guid>ep-2</guid><pubDate>Mon, 08 Sep 2026 07:00:00 +0200</pubDate>
<enclosure url="{server}/2.mp3" type="audio/mpeg" length="1"/></item></channel></rss>'''.encode()


@pytest.fixture
def podcasts(api_client, mocked_player, tmp_path, monkeypatch, audio_server):
    monkeypatch.setattr(lauschkiste.resume, 'ACTIVATION_GRACE_SEC', 0)
    monkeypatch.setattr(lauschkiste.podcasts, 'fetch_feed', lambda url: parse_feed(rss(audio_server)))
    ctrl = Mock()
    ctrl.get_active_backend.return_value = 'local_audio'
    ctrl.playerstatus.return_value = {'state': 'stop'}
    config = {'podcasts': {'podcasts_file': str(tmp_path / 'podcasts.yaml'), 'cache_dir': str(tmp_path / 'feeds'),
                           'state_file': str(tmp_path / 'positions.json'), 'save_interval_sec': 0}}
    with api_client([mocked_player(ctrl), lauschkiste.podcasts.Podcasts, lauschkiste.cache.Cache], config) as client:
        client.post('/api/v1/podcasts', json={'url': f'{audio_server}/feed.xml'})
        yield client, ctrl, audio_server


def episodes(client):
    return {e['title']: e for e in client.get('/api/v1/podcasts/kakadu/episodes').json()}


def download(client, item, timeout=30):
    assert client.post('/api/v1/cache/download', json={'source': 'podcasts', 'item': item}).status_code == 204
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found = [s for s in client.get('/api/v1/cache/downloads').json()['items'] if s['item'] == item]
        if found and found[0]['state'] in ('done', 'error'):
            return found[0]
        time.sleep(0.1)
    raise AssertionError('no result')


def test_episodes_say_where_they_come_from(podcasts):
    client, _, _ = podcasts
    older = episodes(client)['Older']
    assert older['availability'] == 'stream' and older['item'] == f"kakadu~{older['id']}"
    assert download(client, older['item'])['state'] == 'done'
    assert episodes(client)['Older']['availability'] == 'cached'
    assert episodes(client)['Newer']['availability'] == 'stream'


def test_a_downloaded_episode_plays_from_the_box_and_continues_where_the_stream_stopped(podcasts):
    client, ctrl, server = podcasts
    older = episodes(client)['Older']
    client.post('/api/v1/podcasts/play', json={'podcast': 'kakadu', 'episode': older['id']})
    ctrl.play_files.assert_called_once_with([f'{server}/1.mp3'], 0, 0.0, True)
    bus = client.modules.instance('podcasts')._ctx._bus
    bus.publish('player.status', {'state': 'pause', 'file': f'{server}/1.mp3', 'elapsed': '300', 'duration': '750'})

    assert download(client, older['item'])['state'] == 'done'
    path = client.get('/api/v1/cache/files', params={'source': 'podcasts', 'item': older['item']}).json()['files'][0]['path']
    assert open(path, 'rb').read() == AUDIO['/1.mp3']

    bus.publish('player.status', {'state': 'play', 'file': 'music/other.mp3'})
    ctrl.play_files.reset_mock()
    client.post('/api/v1/podcasts/play', json={'podcast': 'kakadu', 'episode': older['id']})
    ctrl.play_files.assert_called_once_with([path], 0, 290.0, True)

    bus.publish('player.status', {'state': 'pause', 'file': path, 'elapsed': '400', 'duration': '750'})
    client.post('/api/v1/cache/remove', json={'source': 'podcasts', 'item': older['item']})
    bus.publish('player.status', {'state': 'play', 'file': 'music/other.mp3'})
    ctrl.play_files.reset_mock()
    client.post('/api/v1/podcasts/play', json={'podcast': 'kakadu', 'episode': older['id']})
    ctrl.play_files.assert_called_once_with([f'{server}/1.mp3'], 0, 390.0, True)


def test_only_heard_episodes_may_be_removed_to_make_room(podcasts):
    client, _, _ = podcasts
    older = episodes(client)['Older']
    provider = client.modules.instance('cache').providers.get('podcasts')
    assert provider.removable(older['item']) is False
    client.post('/api/v1/podcasts/set_heard', json={'podcast': 'kakadu', 'episode': older['id']})
    assert provider.removable(older['item']) is True


def test_deleting_a_podcast_removes_its_downloads(podcasts):
    client, _, _ = podcasts
    older = episodes(client)['Older']
    download(client, older['item'])
    assert client.delete('/api/v1/podcasts/kakadu').status_code == 204
    assert client.get('/api/v1/cache/downloads').json()['items'] == []
