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
    ('shared/settings/cards.yaml', 'settings/cards.yaml'),
    ('../../shared/settings/rfid.yaml', 'settings/rfid.yaml'),
    ('shared', '.'),
    ('../elsewhere/x', '../elsewhere/x'),
])
def test_resolve_relative(home, value, expected):
    assert lauschkiste.paths.resolve(value) == home / expected


def test_resolve_absolute(home):
    assert str(lauschkiste.paths.resolve('/etc/x')) == '/etc/x'


@pytest.mark.parametrize('value', ['default', 'resources/audio/startupsound.wav',
                                   '../../resources/audio/startupsound.wav'])
def test_packaged_sounds(home, value):
    path = sound_path(value, 'startup_sound')
    assert path == lauschkiste.paths.resource('audio', 'startupsound.wav')
    assert path.exists()


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    for name in ('HOME', 'CONF'):
        for key in lauschkiste.paths.env_names(name):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg'))
    lauschkiste.paths.set_home(None)
    yield tmp_path
    lauschkiste.paths.set_home(None)


def test_home_from_new_or_legacy_variable(clean_env, monkeypatch):
    monkeypatch.setenv('JUKEBOX_HOME', str(clean_env / 'old'))
    assert lauschkiste.paths.home() == clean_env / 'old'
    lauschkiste.paths.set_home(None)
    monkeypatch.setenv('LAUSCHKISTE_HOME', str(clean_env / 'new'))
    assert lauschkiste.paths.home() == clean_env / 'new'


def test_default_home_keeps_an_existing_jukebox_directory(clean_env):
    assert lauschkiste.paths.home() == clean_env / 'xdg' / 'lauschkiste'
    lauschkiste.paths.set_home(None)
    (clean_env / 'xdg' / 'jukebox').mkdir(parents=True)
    assert lauschkiste.paths.home() == clean_env / 'xdg' / 'jukebox'
    lauschkiste.paths.set_home(None)
    (clean_env / 'xdg' / 'lauschkiste').mkdir()
    assert lauschkiste.paths.home() == clean_env / 'xdg' / 'lauschkiste'


def test_config_file_falls_back_to_jukebox_yaml(home):
    settings = home / 'settings'
    assert lauschkiste.paths.config_file() == settings / 'lauschkiste.yaml'
    settings.mkdir()
    (settings / 'jukebox.yaml').write_text('{}')
    assert lauschkiste.paths.config_file() == settings / 'jukebox.yaml'
    (settings / 'lauschkiste.yaml').write_text('{}')
    assert lauschkiste.paths.config_file() == settings / 'lauschkiste.yaml'
