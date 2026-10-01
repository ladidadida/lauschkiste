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
