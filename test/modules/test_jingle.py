import signal

import pytest

import lauschkiste.daemon
import lauschkiste.paths
import lauschkiste.jingle
from lauschkiste.contract import OperationError
from lauschkiste.jingle import Jingle


@pytest.fixture
def played(monkeypatch, tmp_path):
    lauschkiste.paths.set_home(tmp_path)
    monkeypatch.setattr(lauschkiste.paths, '_home', tmp_path)
    calls = []
    monkeypatch.setattr(lauschkiste.jingle, 'play_file', lambda path, volume, should_stop=None: calls.append((path, volume)))
    monkeypatch.setattr(lauschkiste.daemon, '_SHUTDOWN_SIGNAL', None)
    return calls


def test_startup_and_shutdown_sounds(start_modules, played, wait_for, tmp_path):
    manager, _ = start_modules([Jingle], {'jingle': {'startup_sound': 'start.wav', 'shutdown_sound': 'stop.wav',
                                                     'volume': 30}})
    assert wait_for(lambda: played == [(str(tmp_path / 'start.wav'), 30)])
    manager.stop()
    assert played[-1] == (str(tmp_path / 'stop.wav'), 30)


def test_default_sounds_are_packaged(start_modules, played, wait_for):
    manager, _ = start_modules([Jingle], {})
    assert wait_for(lambda: played and played[0][0].endswith('resources/audio/startupsound.wav'))
    manager.stop()
    assert played[-1][0].endswith('resources/audio/shutdownsound.wav')


def test_no_shutdown_sound_on_ctrl_c(start_modules, played, monkeypatch):
    manager, _ = start_modules([Jingle], {'jingle': {'startup_sound': '', 'shutdown_sound': 'stop.wav'}})
    monkeypatch.setattr(lauschkiste.daemon, '_SHUTDOWN_SIGNAL', signal.SIGINT)
    manager.stop()
    assert played == []


def test_play_action(start_modules, played, tmp_path, wait_for):
    sound = tmp_path / 'ding.wav'
    sound.write_bytes(b'')
    manager, _ = start_modules([Jingle], {'jingle': {'startup_sound': '', 'shutdown_sound': ''}})
    manager.catalog.call('jingle.play', {'sound': str(sound)})
    assert wait_for(lambda: played == [(str(sound), 100)])
    with pytest.raises(OperationError):
        manager.catalog.call('jingle.play', {'sound': str(tmp_path / 'missing.wav')})
