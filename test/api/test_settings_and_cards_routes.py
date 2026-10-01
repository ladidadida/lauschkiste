from unittest.mock import Mock

import io

import pytest
from ruamel.yaml import YAML

import lauschkiste.cfghandler
from lauschkiste.rfid.cards import Cards
from lauschkiste.system import System


def load_yaml(path):
    return YAML(typ='safe').load(path.read_text())


def dump_yaml(data):
    stream = io.StringIO()
    YAML(typ='safe').dump(data, stream)
    return stream.getvalue()


class QuietSystem(System):
    def start(self, ctx):
        self._ctx = ctx


@pytest.fixture
def main_cfg():
    cfg = lauschkiste.cfghandler.get_handler('jukebox')
    cfg.config_dict({})
    yield cfg
    cfg.config_dict({})


@pytest.fixture
def cards_file(tmp_path):
    path = tmp_path / 'cards.yaml'
    path.write_text(dump_yaml({
        '0001': {'alias': 'play_folder', 'args': ['Rock']},
        '0002': {'package': 'player', 'plugin': 'ctrl', 'method': 'next'},
        '0003': {'alias': 'set_volume', 'args': [12]},
        '0004': {'action': 'player.toggle'},
    }))
    return path


@pytest.fixture
def client(api_client, mocked_player, cards_file, main_cfg):
    ctrl = Mock()
    config = {'cards': {'database': str(cards_file)}}
    with api_client([QuietSystem, mocked_player(ctrl), Cards], config) as test_client:
        test_client.ctrl = ctrl
        yield test_client


def test_get_settings(client, main_cfg):
    response = client.get('/api/v1/settings')
    assert response.status_code == 200
    assert response.json() == {'show_covers': True}


def test_set_settings(client, main_cfg):
    response = client.put('/api/v1/settings', json={'settings': {'show_covers': False}})
    assert response.status_code == 204
    assert main_cfg.getn('webapp', 'show_covers') is False
    assert client.get('/api/v1/settings').json() == {'show_covers': False}


def test_set_settings_rejects_unknown_keys(client):
    response = client.put('/api/v1/settings', json={'settings': {'show_covers': 'maybe'}})
    assert response.status_code == 422


def test_legacy_cards_are_migrated_with_backup(client, cards_file):
    stored = load_yaml(cards_file)
    assert stored['0001'] == {'action': 'player.play_folder', 'args': {'folder': 'Rock'}}
    assert stored['0002'] == {'action': 'player.next', 'args': {}}
    assert stored['0003'] == {'alias': 'set_volume', 'args': [12]}
    backups = list(cards_file.parent.glob('cards.yaml.bak-*'))
    assert len(backups) == 1
    assert load_yaml(backups[0])['0001'] == {'alias': 'play_folder', 'args': ['Rock']}


def test_list_cards(client):
    cards = client.get('/api/v1/cards').json()
    assert cards['0001']['action'] == 'player.play_folder'
    assert cards['0001']['args'] == {'folder': 'Rock'}
    assert cards['0001']['description'] == 'Play a folder of the music library.'
    assert cards['0001']['error'] is None
    assert cards['0003']['action'] is None
    assert cards['0003']['error']


def test_register_card(client, cards_file):
    response = client.post('/api/v1/cards', json={
        'card_id': '0009', 'action': 'player.play_album',
        'args': {'albumartist': 'A', 'album': 'B'}, 'ignore_same_id_delay': True,
    })
    assert response.status_code == 204
    stored = load_yaml(cards_file)['0009']
    assert stored == {'action': 'player.play_album', 'args': {'albumartist': 'A', 'album': 'B'},
                      'ignore_same_id_delay': True, 'ignore_card_removal_action': False}


@pytest.mark.parametrize('body, code', [
    ({'card_id': '0009', 'action': 'player.nope'}, 'invalid_action'),
    ({'card_id': '0009', 'action': 'player.play_folder'}, 'invalid_action'),
    ({'card_id': '0009', 'action': 'player.play_folder', 'args': {'folder': 'x', 'extra': 1}}, 'invalid_action'),
])
def test_register_card_validates_the_action(client, body, code):
    response = client.post('/api/v1/cards', json=body)
    assert response.status_code == 422
    assert response.json()['error']['code'] == code


def test_register_card_needs_overwrite_for_existing_cards(client):
    body = {'card_id': '0004', 'action': 'player.play'}
    assert client.post('/api/v1/cards', json=body).status_code == 409
    assert client.post('/api/v1/cards', json={**body, 'overwrite': True}).status_code == 204


def test_delete_card(client, cards_file):
    assert client.delete('/api/v1/cards/0004').status_code == 204
    assert '0004' not in load_yaml(cards_file)
    response = client.delete('/api/v1/cards/0004')
    assert response.status_code == 404
    assert response.json()['error']['code'] == 'unknown_card'


def test_card_action_runs_through_the_catalog(client):
    card = client.modules.handle('cards').invoke('get_card', '0001')
    client.modules.catalog.call(card.action, card.args)
    client.ctrl.play_folder.assert_called_once_with('Rock', False)
