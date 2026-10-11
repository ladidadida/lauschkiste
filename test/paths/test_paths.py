import pytest

import lauschkiste.common.paths
from lauschkiste.player.jingle import sound_path


@pytest.fixture
def home(tmp_path):
    lauschkiste.common.paths.set_home(tmp_path)
    yield tmp_path
    lauschkiste.common.paths.set_home(None)


@pytest.mark.parametrize('value, expected', [
    ('settings/cards.yaml', 'settings/cards.yaml'),
    ('../elsewhere/x', '../elsewhere/x'),
])
def test_resolve_relative(home, value, expected):
    assert lauschkiste.common.paths.resolve(value) == home / expected


def test_resolve_absolute(home):
    assert str(lauschkiste.common.paths.resolve('/etc/x')) == '/etc/x'


def test_packaged_sounds(home):
    path = sound_path('default', 'startup_sound')
    assert path == lauschkiste.common.paths.resource('audio', 'startupsound.wav')
    assert path.exists()


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    monkeypatch.delenv(lauschkiste.common.paths.HOME_ENV, raising=False)
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg'))
    monkeypatch.setattr(lauschkiste.common.paths, 'is_raspberry_pi', lambda: False)
    lauschkiste.common.paths.set_home(None)
    yield tmp_path
    lauschkiste.common.paths.set_home(None)


def test_home_from_variable_or_xdg(clean_env, monkeypatch):
    assert lauschkiste.common.paths.home() == clean_env / 'xdg' / 'lauschkiste'
    lauschkiste.common.paths.set_home(None)
    monkeypatch.setenv('LAUSCHKISTE_HOME', str(clean_env / 'elsewhere'))
    assert lauschkiste.common.paths.home() == clean_env / 'elsewhere'


def test_config_file(home):
    assert lauschkiste.common.paths.config_file() == home / 'settings' / 'lauschkiste.yaml'


def test_home_on_a_raspberry_pi_is_visible_in_the_user_home(clean_env, monkeypatch):
    monkeypatch.setattr(lauschkiste.common.paths, 'is_raspberry_pi', lambda: True)
    monkeypatch.setenv('HOME', str(clean_env / 'user'))
    assert lauschkiste.common.paths.home() == clean_env / 'user' / 'lauschkiste'
