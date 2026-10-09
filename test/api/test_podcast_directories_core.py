import pytest

import lauschkiste.cache
import lauschkiste.podcasts
from lauschkiste.podcast_opml import normalize_url, parse_opml, render_opml
from lauschkiste.podcasts import parse_feed

FEED = b'''<?xml version="1.0"?><rss version="2.0"><channel><title>Kakadu</title>
<item><title>E</title><guid>1</guid><enclosure url="https://example.org/1.mp3" type="audio/mpeg"/></item></channel></rss>'''

OPML = '''<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0"><head><title>AntennaPod</title></head><body>
  <outline text="Kinder"><outline type="rss" text="Kakadu" title="Kakadu" xmlUrl="https://example.org/kakadu.xml"/></outline>
  <outline type="rss" text="Zwei" xmlUrl="https://example.org/zwei.xml/"/>
  <outline type="rss" text="Kaputt" xmlUrl="ftp://example.org/x"/>
  <outline type="rss" text="Doppelt" xmlUrl="HTTPS://Example.org/kakadu.xml"/>
</body></opml>'''


class Directory:
    def __init__(self, label, rows=(), fail=False):
        self.label, self.rows, self.fail = label, list(rows), fail

    def search(self, term, limit):
        if self.fail:
            raise RuntimeError('down')
        return [dict(row) for row in self.rows][:limit]

    def top(self, limit):
        return self.search('', limit)


def row(title, feed):
    return {'title': title, 'feed_url': feed, 'author': 'A', 'image': None}


@pytest.fixture
def podcasts(api_client, mocked_player, tmp_path, monkeypatch):
    from unittest.mock import Mock
    monkeypatch.setattr(lauschkiste.podcasts, 'fetch_feed', lambda url: parse_feed(FEED))
    ctrl = Mock()
    ctrl.get_active_backend.return_value = 'local_audio'
    ctrl.playerstatus.return_value = {'state': 'stop'}
    config = {'podcasts': {'podcasts_file': str(tmp_path / 'podcasts.yaml'), 'cache_dir': str(tmp_path / 'feeds'),
                           'state_file': str(tmp_path / 'positions.json')}}
    with api_client([mocked_player(ctrl), lauschkiste.podcasts.Podcasts, lauschkiste.cache.Cache], config) as client:
        yield client, client.modules.instance('podcasts').directories


def test_search_merges_directories_takes_turns_and_drops_duplicates(podcasts):
    client, directories = podcasts
    directories.register('one', Directory('One', [row('A1', 'https://a/1'), row('A2', 'https://a/2')]))
    directories.register('two', Directory('Two', [row('B1', 'HTTPS://a/1/'), row('B2', 'https://b/2')]))
    result = client.get('/api/v1/podcasts/search', params={'term': 'x'}).json()
    assert [(h['title'], h['directory']) for h in result['hits']] == [('A1', 'one'), ('A2', 'one'), ('B2', 'two')]
    assert result['errors'] == {}
    assert [d['label'] for d in client.get('/api/v1/podcasts/directories').json()] == ['One', 'Two']
    only = client.get('/api/v1/podcasts/search', params={'term': 'x', 'directory': 'two'}).json()
    assert [h['title'] for h in only['hits']] == ['B1', 'B2']


def test_a_failing_directory_does_not_hide_the_others(podcasts):
    client, directories = podcasts
    directories.register('good', Directory('Good', [row('A1', 'https://a/1')]))
    directories.register('bad', Directory('Bad', fail=True))
    result = client.get('/api/v1/podcasts/top').json()
    assert [h['title'] for h in result['hits']] == ['A1'] and 'down' in result['errors']['bad']


def test_hits_know_what_is_subscribed_already(podcasts):
    client, directories = podcasts
    client.post('/api/v1/podcasts', json={'url': 'https://example.org/kakadu.xml'})
    directories.register('one', Directory('One', [row('Kakadu', 'https://example.org/kakadu.xml/'),
                                                  row('Other', 'https://example.org/other.xml')]))
    hits = client.get('/api/v1/podcasts/search', params={'term': 'k'}).json()['hits']
    assert [(h['title'], h['subscribed']) for h in hits] == [('Kakadu', True), ('Other', False)]


def test_search_without_term_and_unknown_directory(podcasts):
    client, directories = podcasts
    directories.register('one', Directory('One', [row('A1', 'https://a/1')]))
    assert client.get('/api/v1/podcasts/search', params={'term': '  '}).json() == {'hits': [], 'errors': {}}
    assert client.get('/api/v1/podcasts/search', params={'term': 'x', 'directory': 'nope'}).status_code == 404


def test_without_directories_there_is_just_nothing_to_find(podcasts):
    client, _ = podcasts
    assert client.get('/api/v1/podcasts/directories').json() == []
    assert client.get('/api/v1/podcasts/search', params={'term': 'x'}).json() == {'hits': [], 'errors': {}}


def test_opml_import_subscribes_skips_known_and_reports(podcasts):
    client, _ = podcasts
    client.post('/api/v1/podcasts', json={'url': 'https://example.org/kakadu.xml'})
    response = client.post('/api/v1/podcasts/import_opml', json={'content': OPML})
    assert response.status_code == 200
    assert response.json() == {'added': ['Zwei'], 'already_subscribed': 2, 'invalid': 1}
    names = sorted(p['name'] for p in client.get('/api/v1/podcasts').json())
    assert names == ['Kakadu', 'Zwei']


def test_invalid_opml_is_rejected(podcasts):
    client, _ = podcasts
    assert client.post('/api/v1/podcasts/import_opml', json={'content': 'nope'}).status_code == 422
    assert client.post('/api/v1/podcasts/import_opml', json={'content': '<rss/>'}).status_code == 422


def test_opml_export_round_trips(podcasts):
    client, _ = podcasts
    client.post('/api/v1/podcasts', json={'url': 'https://example.org/kakadu.xml'})
    content = client.get('/api/v1/podcasts/export_opml').json()['content']
    assert content.startswith('<?xml') and parse_opml(content) == [
        {'title': 'Kakadu', 'url': 'https://example.org/kakadu.xml'}]


def test_opml_helpers():
    assert normalize_url('HTTPS://Example.org/Path/?a=1#x') == 'https://example.org/Path?a=1'
    assert parse_opml(render_opml([('A & B', 'https://a/feed?x=1&y=2')])) == [
        {'title': 'A & B', 'url': 'https://a/feed?x=1&y=2'}]
