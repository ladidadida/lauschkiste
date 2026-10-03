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
                       'version': '1.2', 'summary': 'Does things.', 'problem': None, 'missing_extras': []}]
    assert client.put('/api/v1/plugins/gadget', json={'enabled': True}).json()['enabled'] is True
    assert client.modules.settings.cfg.getn('plugins') == {'gadget': {}}
    assert 'gadget' in client.get('/api/v1/settings/restart').json()['modules']
    assert client.put('/api/v1/plugins/gadget', json={'enabled': False}).json()['enabled'] is False
    assert client.put('/api/v1/plugins/missing', json={'enabled': True}).status_code == 404
