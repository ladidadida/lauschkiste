from typing import Optional
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, Field

import lauschkiste.contract.plugins as plugins
from lauschkiste.contract import ActionEntry, CoreModule, query


class DemoSettings(BaseModel):
    level: int = Field(3, ge=0, le=10)
    name: str = 'box'
    action: Optional[ActionEntry] = None


class Demo(CoreModule):
    """Demo module."""

    name = 'demo'
    settings = DemoSettings
    applied = []

    def settings_changed(self, changed):
        Demo.applied.append(changed)
        return 'name' not in changed

    @query()
    def ping(self) -> str:
        return 'pong'


@pytest.fixture
def client(api_client):
    Demo.applied = []
    with api_client([Demo], {'demo': {'level': 99, 'other': 'kept'}}) as client:
        yield client


def test_settings_are_listed_with_schema_and_values(client):
    entries = {entry['name']: entry for entry in client.get('/api/v1/settings/modules').json()}
    demo = entries['demo']
    assert demo['title'] == 'Demo module.'
    assert demo['values'] == {'level': 3, 'name': 'box', 'action': None}
    assert demo['schema']['properties']['level']['maximum'] == 10
    assert demo['schema']['$defs']['ActionEntry']['widget'] == 'action'


def test_update_validates_stores_and_reports_restart(client):
    response = client.put('/api/v1/settings/modules/demo', json={'values': {'level': 7}})
    assert response.status_code == 200
    assert response.json()['values']['level'] == 7
    assert response.json()['restart_required'] is False
    assert Demo.applied == [{'level': 7}]
    cfg = client.modules.settings.cfg
    assert cfg.getn('demo', 'level') == 7 and cfg.getn('demo', 'other') == 'kept'

    assert client.put('/api/v1/settings/modules/demo', json={'values': {'name': 'x'}}).json()['restart_required']
    assert client.get('/api/v1/settings/restart').json() == {'required': True, 'modules': ['demo']}


def test_action_entries_and_none_values(client):
    entry = {'action': 'demo.ping', 'args': {}}
    assert client.put('/api/v1/settings/modules/demo', json={'values': {'action': entry}}).json()['values'][
        'action'] == entry
    assert client.put('/api/v1/settings/modules/demo', json={'values': {'action': None}}).json()['values'][
        'action'] is None
    assert 'action' not in client.modules.settings.cfg.getn('demo')


@pytest.mark.parametrize('values, code', [
    ({'level': 11}, 'invalid_setting'),
    ({'nope': 1}, 'unknown_setting'),
])
def test_invalid_updates_are_rejected(client, values, code):
    response = client.put('/api/v1/settings/modules/demo', json={'values': values})
    assert response.status_code == 422
    assert response.json()['error']['code'] == code


def test_unknown_module(client):
    assert client.get('/api/v1/settings/modules/nope').status_code == 404


def test_plugins_list_and_enable(client, monkeypatch):
    ep = Mock(dist=Mock(version='1.2'), load=Mock(return_value=type('P', (), {'__doc__': 'Does things.'})))
    ep.name = 'gadget'
    ep.dist.name = 'lauschkiste-plugin-gadget'
    monkeypatch.setattr(plugins, 'installed', lambda: {'gadget': ep})
    monkeypatch.setattr(plugins, 'missing_extras', lambda name: [])
    listed = client.get('/api/v1/plugins').json()
    assert listed == [{'name': 'gadget', 'enabled': False, 'running': False, 'package': 'lauschkiste-plugin-gadget',
                       'version': '1.2', 'summary': 'Does things.', 'problem': None, 'missing_extras': [],
                       'installing': False, 'install_error': None}]
    assert client.put('/api/v1/plugins/gadget', json={'enabled': True}).json()['enabled'] is True
    assert client.modules.settings.cfg.getn('plugins') == {'gadget': {}}
    assert 'gadget' in client.get('/api/v1/settings/restart').json()['modules']
    assert client.put('/api/v1/plugins/gadget', json={'enabled': False}).json()['enabled'] is False
    assert client.put('/api/v1/plugins/missing', json={'enabled': True}).status_code == 404


class Elsewhere(CoreModule):
    """Keeps its settings in another file."""

    name = 'elsewhere'
    settings = DemoSettings
    store = None

    def settings_storage(self):
        return Elsewhere.store, ('section',)

    @query()
    def ping(self) -> str:
        return 'pong'


def test_settings_kept_in_another_config(api_client):
    from lauschkiste.cfghandler import ConfigHandler
    Elsewhere.store = ConfigHandler('elsewhere-test')
    Elsewhere.store.config_dict({'section': {'level': 5, 'driver': 'kept'}})
    with api_client([Elsewhere], {}) as client:
        assert client.get('/api/v1/settings/modules/elsewhere').json()['values']['level'] == 5
        client.put('/api/v1/settings/modules/elsewhere', json={'values': {'level': 6}})
        assert Elsewhere.store.getn('section') == {'level': 6, 'driver': 'kept'}
        assert client.modules.settings.cfg.getn('elsewhere', default=None) is None


def test_install_missing_extras_in_the_background(client, monkeypatch):
    import sys
    import time
    ep = Mock(dist=Mock(version='1.0'), load=Mock(return_value=type('P', (), {'__doc__': 'Gadget.'})))
    ep.name = 'gadget'
    ep.dist.name = 'lauschkiste-plugin-gadget'
    missing = ['lauschkiste-plugin-gadget[hw]']
    monkeypatch.setattr(plugins, 'installed', lambda: {'gadget': ep})
    monkeypatch.setattr(plugins, 'missing_extras', lambda name: list(missing))
    monkeypatch.setattr(plugins, 'install_command', lambda requirements: [sys.executable, '-c', 'pass'])

    response = client.post('/api/v1/plugins/gadget/extras')
    assert response.status_code == 202 and response.json()['installing'] is True
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and client.get('/api/v1/plugins').json()[0]['installing']:
        time.sleep(0.05)
    missing.clear()
    entry = client.get('/api/v1/plugins').json()[0]
    assert (entry['installing'], entry['install_error'], entry['missing_extras']) == (False, None, [])
    assert 'gadget' in client.get('/api/v1/settings/restart').json()['modules']
    assert client.post('/api/v1/plugins/gadget/extras').status_code == 409


def test_failed_installation_is_reported(client, monkeypatch):
    import sys
    import time
    ep = Mock(dist=Mock(version='1.0'), load=Mock(return_value=type('P', (), {'__doc__': 'Gadget.'})))
    ep.name = 'gadget'
    ep.dist.name = 'lauschkiste-plugin-gadget'
    monkeypatch.setattr(plugins, 'installed', lambda: {'gadget': ep})
    monkeypatch.setattr(plugins, 'missing_extras', lambda name: ['x[y]'])
    monkeypatch.setattr(plugins, 'install_command',
                        lambda requirements: [sys.executable, '-c', 'import sys; sys.exit("no network")'])
    client.post('/api/v1/plugins/gadget/extras')
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and client.get('/api/v1/plugins').json()[0]['installing']:
        time.sleep(0.05)
    assert client.get('/api/v1/plugins').json()[0]['install_error'] == 'no network'
