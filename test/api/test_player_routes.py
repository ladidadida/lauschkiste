from unittest.mock import Mock

import pytest



@pytest.fixture
def player_ctrl():
    ctrl = Mock()
    ctrl.get_volume.return_value = 42
    ctrl.set_volume.return_value = 55
    ctrl.playerstatus.return_value = {'state': 'play', 'song': '0', 'file': 'a.mp3', 'elapsed': '1.5',
                                      'random': '1', 'volume': '42'}
    ctrl.get_active_backend.return_value = 'local_audio'
    return ctrl


@pytest.fixture
def client(player_ctrl, api_client, mocked_player):
    with api_client([mocked_player(player_ctrl)]) as test_client:
        yield test_client


def test_play(client, player_ctrl):
    response = client.post('/api/v1/player/play')
    assert response.status_code == 204
    player_ctrl.play.assert_called_once_with()


def test_pause_defaults_to_state_1(client, player_ctrl):
    response = client.post('/api/v1/player/pause', json={})
    assert response.status_code == 204
    player_ctrl.pause.assert_called_once_with(1)


def test_pause_with_explicit_state(client, player_ctrl):
    response = client.post('/api/v1/player/pause', json={'state': 0})
    assert response.status_code == 204
    player_ctrl.pause.assert_called_once_with(0)


def test_toggle(client, player_ctrl):
    response = client.post('/api/v1/player/toggle')
    assert response.status_code == 204
    player_ctrl.toggle.assert_called_once_with()


def test_next(client, player_ctrl):
    response = client.post('/api/v1/player/next')
    assert response.status_code == 204
    player_ctrl.next.assert_called_once_with()


def test_prev(client, player_ctrl):
    response = client.post('/api/v1/player/prev')
    assert response.status_code == 204
    player_ctrl.prev.assert_called_once_with()


def test_seek(client, player_ctrl):
    response = client.post('/api/v1/player/seek', json={'position': 12.5})
    assert response.status_code == 204
    player_ctrl.seek.assert_called_once_with(12.5)


def test_seek_requires_position(client, player_ctrl):
    response = client.post('/api/v1/player/seek', json={})
    assert response.status_code == 422
    player_ctrl.seek.assert_not_called()


def test_shuffle_defaults_to_toggle(client, player_ctrl):
    response = client.post('/api/v1/player/shuffle', json={})
    assert response.status_code == 204
    player_ctrl.shuffle.assert_called_once_with('toggle')


def test_repeat_with_explicit_option(client, player_ctrl):
    response = client.post('/api/v1/player/repeat', json={'option': 'enable_repeat'})
    assert response.status_code == 204
    player_ctrl.repeat.assert_called_once_with('enable_repeat')


def test_play_folder(client, player_ctrl):
    response = client.post('/api/v1/player/folder', json={'folder': 'Stories', 'recursive': True})
    assert response.status_code == 204
    player_ctrl.play_folder.assert_called_once_with('Stories', True)


def test_play_folder_recursive_defaults_to_false(client, player_ctrl):
    response = client.post('/api/v1/player/folder', json={'folder': 'Stories'})
    assert response.status_code == 204
    player_ctrl.play_folder.assert_called_once_with('Stories', False)


def test_play_song(client, player_ctrl):
    response = client.post('/api/v1/player/song', json={'song_url': 'Stories/01.mp3'})
    assert response.status_code == 204
    player_ctrl.play_single.assert_called_once_with('Stories/01.mp3', None)


def test_get_status(client, player_ctrl):
    response = client.get('/api/v1/player/status')
    assert response.status_code == 200
    status = response.json()
    assert status['provider'] == 'local_audio'
    assert status['state'] == 'play'
    assert status['position'] == 0
    assert status['file'] == 'a.mp3'
    assert status['elapsed'] == 1.5
    assert status['random'] is True
    assert 'volume' not in status


def test_get_volume(client, player_ctrl):
    response = client.get('/api/v1/player/volume')
    assert response.status_code == 200
    assert response.json() == {'volume': 42}


def test_set_volume(client, player_ctrl):
    response = client.put('/api/v1/player/volume', json={'volume': 55})
    assert response.status_code == 200
    assert response.json() == {'volume': 55}
    player_ctrl.set_volume.assert_called_once_with(55)


def test_player_routes_appear_in_openapi_schema(client):
    schema = client.get('/openapi.json').json()
    assert '/api/v1/player/play' in schema['paths']
    assert '/api/v1/player/volume' in schema['paths']
    status = schema['paths']['/api/v1/player/status']['get']['responses']['200']
    assert status['content']['application/json']['schema'] == {'$ref': '#/components/schemas/PlayerStatus'}
    assert 'PlayerStatus' in schema['components']['schemas']
