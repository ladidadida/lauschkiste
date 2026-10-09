from unittest.mock import Mock

import pytest

import lauschkiste.radio
from lauschkiste.radio_playlist import parse_stations, render_m3u

M3U = '''#EXTM3U
#EXTINF:-1,Kinderradio
https://example.org/kids.mp3
#EXTINF:-1,Nachrichten
HTTPS://Example.org/news.mp3
https://example.org/ohne-name.aac
ftp://example.org/falsch
'''

PLS = '''[playlist]
NumberOfEntries=2
File1=https://example.org/a.mp3
Title1=Radio A
File2=https://example.org/b.mp3
Length2=-1
'''


class Directory:
    def __init__(self, label, rows=(), fail=False):
        self.label, self.rows, self.fail = label, list(rows), fail

    def search(self, term, limit):
        if self.fail:
            raise RuntimeError('down')
        return [dict(row) for row in self.rows][:limit]

    def top(self, limit):
        return self.search('', limit)


def row(name, url, **more):
    return {'name': name, 'url': url, **more}


@pytest.fixture
def radio(api_client, mocked_player, tmp_path):
    config = {'radio': {'stations_file': str(tmp_path / 'radio.yaml')}}
    with api_client([mocked_player(Mock()), lauschkiste.radio.Radio], config) as client:
        yield client, client.modules.instance('radio').directories


def test_search_merges_takes_turns_drops_duplicates_and_marks_added(radio):
    client, directories = radio
    client.post('/api/v1/radio/stations', json={'name': 'Kids', 'url': 'https://a/1'})
    directories.register('one', Directory('One', [row('A1', 'https://a/1', codec='MP3', bitrate=128),
                                                  row('A2', 'https://a/2')]))
    directories.register('two', Directory('Two', [row('B1', 'HTTPS://a/2/'), row('B2', 'https://b/2')]))
    result = client.get('/api/v1/radio/search', params={'term': 'x'}).json()
    assert [h['name'] for h in result['hits']] == ['A1', 'B1', 'B2']
    assert result['hits'][0]['added'] is True and result['hits'][0]['codec'] == 'MP3'
    assert [d['label'] for d in client.get('/api/v1/radio/directories').json()] == ['One', 'Two']


def test_a_failing_directory_and_an_unknown_one(radio):
    client, directories = radio
    directories.register('good', Directory('Good', [row('A1', 'https://a/1')]))
    directories.register('bad', Directory('Bad', fail=True))
    result = client.get('/api/v1/radio/top').json()
    assert [h['name'] for h in result['hits']] == ['A1'] and 'down' in result['errors']['bad']
    assert client.get('/api/v1/radio/search', params={'term': 'x', 'directory': 'nope'}).status_code == 404
    assert client.get('/api/v1/radio/search', params={'term': ' '}).json() == {'hits': [], 'errors': {}}


def test_without_directories_there_is_nothing_to_find(radio):
    client, _ = radio
    assert client.get('/api/v1/radio/directories').json() == []
    assert client.get('/api/v1/radio/search', params={'term': 'x'}).json() == {'hits': [], 'errors': {}}


def test_import_m3u_adds_new_streams_and_skips_known_and_invalid(radio):
    client, _ = radio
    client.post('/api/v1/radio/stations', json={'name': 'Kinderradio', 'url': 'https://example.org/kids.mp3/'})
    response = client.post('/api/v1/radio/import_playlist', json={'content': M3U})
    assert response.json() == {'added': ['Nachrichten', 'example.org'], 'already_there': 1, 'invalid': 0}
    names = sorted(s['name'] for s in client.get('/api/v1/radio/stations').json())
    assert names == ['Kinderradio', 'Nachrichten', 'example.org']


def test_import_pls_and_bad_files(radio):
    client, _ = radio
    assert client.post('/api/v1/radio/import_playlist', json={'content': PLS}).json()['added'] == [
        'Radio A', 'example.org']
    assert client.post('/api/v1/radio/import_playlist', json={'content': 'nothing here'}).status_code == 422


def test_export_m3u_round_trips(radio):
    client, _ = radio
    client.post('/api/v1/radio/stations', json={'name': 'Kinderradio', 'url': 'https://example.org/kids.mp3'})
    content = client.get('/api/v1/radio/export_playlist').json()['content']
    assert content == '#EXTM3U\n#EXTINF:-1,Kinderradio\nhttps://example.org/kids.mp3\n'
    assert parse_stations(content) == [{'name': 'Kinderradio', 'url': 'https://example.org/kids.mp3'}]


def test_playlist_helpers():
    assert parse_stations(render_m3u([{'name': 'A, B', 'url': 'https://a/b'}])) == [{'name': 'A, B', 'url': 'https://a/b'}]
    with pytest.raises(ValueError):
        parse_stations('#EXTM3U\n')
