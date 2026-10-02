import pytest

import lauschkiste.paths
from lauschkiste.jingle import sound_path


@pytest.fixture
def home(tmp_path):
    lauschkiste.paths.set_home(tmp_path)
    yield tmp_path
    lauschkiste.paths.set_home(None)


@pytest.mark.parametrize('value, expected', [
    ('settings/cards.yaml', 'settings/cards.yaml'),
    ('../elsewhere/x', '../elsewhere/x'),
])
def test_resolve_relative(home, value, expected):
    assert lauschkiste.paths.resolve(value) == home / expected


def test_resolve_absolute(home):
    assert str(lauschkiste.paths.resolve('/etc/x')) == '/etc/x'


def test_packaged_sounds(home):
    path = sound_path('default', 'startup_sound')
    assert path == lauschkiste.paths.resource('audio', 'startupsound.wav')
    assert path.exists()


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    monkeypatch.delenv(lauschkiste.paths.HOME_ENV, raising=False)
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg'))
    lauschkiste.paths.set_home(None)
    yield tmp_path
    lauschkiste.paths.set_home(None)


def test_home_from_variable_or_xdg(clean_env, monkeypatch):
    assert lauschkiste.paths.home() == clean_env / 'xdg' / 'lauschkiste'
    lauschkiste.paths.set_home(None)
    monkeypatch.setenv('LAUSCHKISTE_HOME', str(clean_env / 'elsewhere'))
    assert lauschkiste.paths.home() == clean_env / 'elsewhere'


def test_config_file(home):
    assert lauschkiste.paths.config_file() == home / 'settings' / 'lauschkiste.yaml'
