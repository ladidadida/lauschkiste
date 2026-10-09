import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

pytest.importorskip('lauschkiste_plugin_podcast_directories', reason="the podcast-directories plugin is not installed")

from lauschkiste_plugin_podcast_directories import PodcastDirectories
from lauschkiste_plugin_podcast_directories.directories import (DirectoryError, Fyyd, ITunes, JsonDirectory,
                                                                PodcastIndex)

ROUTES = {}
SEEN = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        parts = urlsplit(self.path)
        SEEN.append((parts.path, parse_qs(parts.query), dict(self.headers)))
        body = ROUTES.get(parts.path)
        if body is None:
            self.send_response(404)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture
def server():
    ROUTES.clear()
    SEEN.clear()
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{httpd.server_port}'
    httpd.shutdown()


def test_itunes_search_and_top_list(server):
    ROUTES['/search'] = {'results': [{'collectionName': 'Kakadu', 'feedUrl': 'https://k/feed', 'artistName': 'DLF',
                                      'artworkUrl600': 'https://k/600.jpg', 'artworkUrl100': 'https://k/100.jpg'}]}
    ROUTES['/de/rss/toppodcasts/limit=2/json'] = {'feed': {'entry': [{'id': {'attributes': {'im:id': '2'}}},
                                                                    {'id': {'attributes': {'im:id': '1'}}}]}}
    ROUTES['/lookup'] = {'results': [{'collectionId': 1, 'collectionName': 'One', 'feedUrl': 'https://one'},
                                     {'collectionId': 2, 'collectionName': 'Two', 'feedUrl': 'https://two'}]}
    directory = ITunes('Apple', url=server, country='DE')
    assert directory.search('kakadu', 5) == [{'title': 'Kakadu', 'feed_url': 'https://k/feed', 'author': 'DLF',
                                              'image': 'https://k/600.jpg'}]
    assert SEEN[0][1] == {'term': ['kakadu'], 'media': ['podcast'], 'entity': ['podcast'], 'country': ['de'],
                          'limit': ['5']}
    assert [r['title'] for r in directory.top(2)] == ['Two', 'One']
    assert SEEN[-1][1] == {'id': ['2,1'], 'entity': ['podcast']}


def test_fyyd_search_and_hot(server):
    row = {'title': 'Kakadu', 'xmlURL': 'https://k/feed', 'author': 'DLF', 'imgURL': 'https://k/i.jpg'}
    ROUTES['/0.2/search/podcast'] = {'status': 1, 'data': [row]}
    ROUTES['/0.2/feature/podcast/hot'] = {'status': 1, 'data': [row]}
    directory = Fyyd('fyyd', url=server, language='de')
    assert directory.search('kakadu', 3)[0] == {'title': 'Kakadu', 'feed_url': 'https://k/feed', 'author': 'DLF',
                                                'image': 'https://k/i.jpg'}
    assert SEEN[0][1] == {'title': ['kakadu'], 'count': ['3']}
    assert directory.top(4)[0]['feed_url'] == 'https://k/feed'
    assert SEEN[1][1] == {'count': ['4'], 'language': ['de']}


def test_podcast_index_signs_its_requests_and_needs_a_key(server):
    ROUTES['/api/1.0/search/byterm'] = {'feeds': [{'title': 'Kakadu', 'url': 'https://k/feed', 'author': 'DLF',
                                                    'image': 'https://k/i.jpg'}]}
    with pytest.raises(DirectoryError, match='API key'):
        PodcastIndex('Index', url=server).search('kakadu', 5)
    directory = PodcastIndex('Index', url=server, key=lambda: 'KEY', secret=lambda: 'SECRET')
    assert directory.search('kakadu', 5)[0]['feed_url'] == 'https://k/feed'
    headers = {k.lower(): v for k, v in SEEN[-1][2].items()}
    assert headers['x-auth-key'] == 'KEY'
    assert headers['authorization'] == hashlib.sha1(('KEY' + 'SECRET' + headers['x-auth-date']).encode()).hexdigest()


def test_a_generic_json_directory(server):
    ROUTES['/find'] = {'data': {'items': [{'name': 'Mein Podcast', 'rss': 'https://m/feed', 'by': 'Ich'}]}}
    directory = JsonDirectory('Mine', search_url=server + '/find?q={term}&n={limit}', results='data.items',
                              title_key='name', feed_key='rss', author_key='by')
    assert directory.search('mein podcast', 7) == [{'title': 'Mein Podcast', 'feed_url': 'https://m/feed',
                                                    'author': 'Ich', 'image': None}]
    assert SEEN[0][1] == {'q': ['mein podcast'], 'n': ['7']}
    assert directory.top(5) == []
    ROUTES['/find'] = {'other': 1}
    with pytest.raises(DirectoryError, match='no list'):
        directory.search('x', 1)


def test_errors_are_plain(server):
    with pytest.raises(DirectoryError, match='not reachable'):
        ITunes('A', url=server).search('x', 1)  # 404
    ROUTES['/search'] = b'<html>'
    with pytest.raises(DirectoryError, match='not JSON'):
        ITunes('A', url=server).search('x', 1)


def test_settings_default_to_apple_and_fyyd_on_and_the_index_off():
    from lauschkiste_plugin_podcast_directories import default_directories
    defaults = default_directories()
    assert {k: v.enabled for k, v in defaults.items()} == {'itunes': True, 'fyyd': True, 'podcastindex': False}
    assert PodcastDirectories.settings.model_json_schema()['properties']['podcastindex_key']['secret'] is True
