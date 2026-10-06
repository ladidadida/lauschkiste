from unittest.mock import Mock

import pytest

import lauschkiste.radio
from lauschkiste.radio import streams_in_playlist


@pytest.fixture
def radio(api_client, mocked_player, tmp_path):
    ctrl = Mock()
    config = {'radio': {'stations_file': str(tmp_path / 'radio.yaml')}}
    with api_client([mocked_player(ctrl), lauschkiste.radio.Radio], config) as client:
        yield client, ctrl, tmp_path / 'radio.yaml'


def add(client, **body):
    return client.post('/api/v1/radio/stations', json=body)


def test_add_list_update_delete(radio):
    client, _, stations_file = radio
    response = add(client, name='Deutschlandfunk Kultur', url='https://example.org/dlf.mp3')
    assert response.status_code == 201
    assert response.json() == {'id': 'deutschlandfunk-kultur', 'name': 'Deutschlandfunk Kultur',
                               'url': 'https://example.org/dlf.mp3', 'logo': None}
    assert add(client, name='Deutschlandfunk Kultur', url='https://example.org/2.mp3').json()['id'] == \
        'deutschlandfunk-kultur-2'
    assert add(client, name='Hörspaß für Kinder', url='http://example.org/kids').json()['id'] == 'horspass-fur-kinder'
    assert 'horspass-fur-kinder' in stations_file.read_text()

    response = client.put('/api/v1/radio/stations/horspass-fur-kinder',
                          json={'name': 'Kinderradio', 'logo': 'https://example.org/logo.png'})
    assert response.json()['name'] == 'Kinderradio' and response.json()['logo'] == 'https://example.org/logo.png'
    assert client.put('/api/v1/radio/stations/horspass-fur-kinder', json={'logo': ''}).json()['logo'] is None

    assert client.delete('/api/v1/radio/stations/deutschlandfunk-kultur-2').status_code == 204
    names = [s['name'] for s in client.get('/api/v1/radio/stations').json()]
    assert names == ['Deutschlandfunk Kultur', 'Kinderradio']


def test_stations_are_loaded_on_start(api_client, mocked_player, tmp_path):
    (tmp_path / 'radio.yaml').write_text("stations:\n  wdr:\n    name: WDR 5\n    url: https://example.org/wdr5\n"
                                         "  broken: nothing\n")
    config = {'radio': {'stations_file': str(tmp_path / 'radio.yaml')}}
    with api_client([mocked_player(Mock()), lauschkiste.radio.Radio], config) as client:
        assert client.get('/api/v1/radio/stations').json() == [
            {'id': 'wdr', 'name': 'WDR 5', 'url': 'https://example.org/wdr5', 'logo': None}]


@pytest.mark.parametrize('body', [
    {'name': 'X', 'url': 'file:///etc/passwd'},
    {'name': 'X', 'url': 'example.org/stream'},
    {'name': ' ', 'url': 'https://example.org/stream'},
    {'name': 'X', 'url': 'https://example.org/stream', 'logo': 'javascript:alert(1)'},
])
def test_invalid_stations_are_rejected(radio, body):
    client, _, _ = radio
    assert add(client, **body).status_code == 422


def test_play_station(radio):
    client, ctrl, _ = radio
    station = add(client, name='Stream', url='https://example.org/live.mp3').json()['id']
    assert client.post('/api/v1/radio/play', json={'station': station}).status_code == 204
    ctrl.play_files.assert_called_once_with(['https://example.org/live.mp3'], 0, 0.0, False)
    ctrl.get_active_backend.return_value = 'local_audio'
    ctrl.playerstatus.return_value = {'state': 'play', 'file': 'https://example.org/live.mp3', 'song': '0'}
    assert client.get('/api/v1/player/status').json()['context'] == {
        'kind': 'radio', 'title': 'Stream', 'action': 'radio.play', 'args': {'station': station}}
    assert client.post('/api/v1/radio/play', json={'station': 'nope'}).status_code == 404


def test_play_resolves_playlists(radio, monkeypatch):
    client, ctrl, _ = radio
    response = Mock()
    response.raw.read.return_value = b'[playlist]\nFile1=https://example.org/real.aac\nTitle1=Live\n'
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    monkeypatch.setattr('requests.get', Mock(return_value=response))
    station = add(client, name='Playlist', url='https://example.org/station.pls').json()['id']
    client.post('/api/v1/radio/play', json={'station': station})
    ctrl.play_files.assert_called_once_with(['https://example.org/real.aac'], 0, 0.0, False)


def test_streams_in_playlist():
    assert streams_in_playlist('#EXTM3U\n#EXTINF:-1,Radio\nhttp://a/1\n\nhttps://a/2\nlocal.mp3\n') == \
        ['http://a/1', 'https://a/2']
    assert streams_in_playlist('[playlist]\nNumberOfEntries=1\nFile1=http://b/x\n') == ['http://b/x']
