from pydantic import BaseModel, Field

from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract import CoreModule
from lauschkiste.contract.context import ModuleConfig
from lauschkiste.contract.secrets import SecretStore, secrets_path
from lauschkiste.contract.settings import secret_fields


class Settings(BaseModel):
    name: str = 'box'
    token: str = Field('', json_schema_extra={'secret': True})


class Demo(CoreModule):
    name = 'demo'
    settings = Settings


def test_secret_fields_are_found():
    assert secret_fields(Settings) == {'token'}


def test_the_store_persists_with_private_permissions(tmp_path):
    path = tmp_path / 'settings' / 'secrets.yaml'
    store = SecretStore(path)
    store.set('plugins', 'demo', 'token', value='abc')
    assert oct(path.stat().st_mode & 0o777) == '0o600'
    assert SecretStore(path).get('plugins', 'demo', 'token') == 'abc'
    store.set('plugins', 'demo', 'token', value='')
    assert SecretStore(path).get('plugins', 'demo', 'token') is None


def test_secrets_path_is_next_to_the_config():
    assert str(secrets_path('/home/x/settings/lauschkiste.yaml')) == '/home/x/settings/secrets.yaml'
    assert secrets_path(None) is None


def test_modules_read_secrets_like_other_settings(tmp_path):
    cfg = ConfigHandler('test')
    cfg.config_dict({'demo': {'name': 'x', 'token': 'old-value-in-the-main-config'}})
    store = SecretStore(tmp_path / 'secrets.yaml')
    store.set('demo', 'token', value='from-secrets')
    config = ModuleConfig(cfg, ('demo',))._use_secrets(store, secret_fields(Settings))
    assert config.get('token') == 'from-secrets'
    assert config.get('name') == 'x'
    assert config.as_dict() == {'name': 'x', 'token': 'from-secrets'}
