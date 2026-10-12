from unittest.mock import Mock

import pytest


@pytest.fixture
def player_ctrl():
    ctrl = Mock()
    ctrl.list_backends.return_value = ['local_audio', 'main']
    ctrl.get_active_backend.return_value = 'local_audio'
    ctrl.get_default_backend.return_value = 'local_audio'
    ctrl.select_backend.return_value = 'main'
    return ctrl


@pytest.fixture
def client(player_ctrl, api_client, mocked_player):
    with api_client([mocked_player(player_ctrl)]) as test_client:
        yield test_client


def test_stop(client, player_ctrl):
    response = client.post('/api/v1/player/stop')
    assert response.status_code == 204
    player_ctrl.stop.assert_called_once_with()


def test_rewind(client, player_ctrl):
    response = client.post('/api/v1/player/rewind')
    assert response.status_code == 204
    player_ctrl.rewind.assert_called_once_with()


def test_resume(client, player_ctrl):
    response = client.post('/api/v1/player/resume')
    assert response.status_code == 204
    player_ctrl.resume.assert_called_once_with()


def test_list_backends(client, player_ctrl):
    response = client.get('/api/v1/player/backends')
    assert response.status_code == 200
    assert response.json() == ['local_audio', 'main']


def test_get_active_backend(client, player_ctrl):
    response = client.get('/api/v1/player/backends/active')
    assert response.status_code == 200
    assert response.json() == {'name': 'local_audio'}


def test_get_default_backend(client, player_ctrl):
    response = client.get('/api/v1/player/backends/default')
    assert response.status_code == 200
    assert response.json() == {'name': 'local_audio'}


def test_select_backend(client, player_ctrl):
    response = client.put('/api/v1/player/backends/active', json={'name': 'main'})
    assert response.status_code == 200
    assert response.json() == {'name': 'main'}
    player_ctrl.select_backend.assert_called_once_with('main')


def test_backend_specific_method_not_implemented_maps_to_501(client, player_ctrl):
    # e.g. local_audio doesn't implement resume/coverart -- PlayerCoordinator raises
    # NotImplementedError, not a raw 500.
    player_ctrl.resume.side_effect = NotImplementedError(
        "Player backend 'PlayerLocalAudio' does not support 'resume'")

    response = client.post('/api/v1/player/resume')

    assert response.status_code == 501
