from unittest.mock import Mock

import pytest

import lauschkiste.content.library
from lauschkiste.common.cfghandler import ConfigHandler
from lauschkiste.common.publishing.bus import EventBus
from lauschkiste.content.library.module import Library
from lauschkiste.content.playlists import Playlists, parse_m3u, render_m3u
from lauschkiste.contract import OperationError
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.player.module import Player

from test.content.test_audiobooks import wait_for, write_flac


@pytest.fixture
def setup(tmp_path, monkeypatch):
    library_dir = tmp_path / 'library'
    write_flac(library_dir / 'music' / 'Rock' / '01.flac', title='Loud', artist='Band', album='Rock')
    write_flac(library_dir / 'music' / 'Rock' / '02.flac', title='Louder', artist='Band', album='Rock')
    write_flac(library_dir / 'music' / 'Pop' / '01.flac', title='Sweet')
    monkeypatch.setattr(lauschkiste.content.library, 'root', lambda: str(library_dir))
    ctrl = Mock()
    ctrl.get_active_backend.return_value = 'local_audio'
    ctrl.playerstatus.return_value = {'state': 'stop'}

    class TestPlayer(Player):
        def start(self, ctx):
            self._ctx = ctx
            self._coordinator = ctrl

        def ready(self):
            pass

        def stop(self):
            return []

    cfg = ConfigHandler('test')
    cfg.config_dict({'library': {'path': str(library_dir), 'index': str(tmp_path / 'index.sqlite'),
                                 'cover_cache': str(tmp_path / 'covers'), 'watch': False},
                     'playlists': {'folder': str(tmp_path / 'playlists')}})
    bus = EventBus()
    events = []
    bus.register(lambda topic, payload: events.append((topic, payload)))
    manager = ModuleManager([Library, TestPlayer, Playlists], cfg, bus, plugins={}, strict=True)
    manager.load()
    manager.start()
    manager.ready()
    assert wait_for(lambda: any(topic == 'library.scanned' for topic, _ in events))
    yield manager, ctrl, tmp_path / 'playlists', events
    manager.stop()


def test_m3u_round_trip():
    text = render_m3u('Für Emma', ['music/a.mp3', 'https://example.org/b.mp3'])
    assert parse_m3u(text, 'x') == ('Für Emma', ['music/a.mp3', 'https://example.org/b.mp3'])
    assert parse_m3u('#EXTM3U\n#EXTINF:1,a\nmusic/a.mp3\n', 'fallback') == ('fallback', ['music/a.mp3'])


def test_create_change_and_delete_a_playlist(setup):
    manager, _, folder, events = setup
    playlists = manager.handle('playlists')
    created = playlists.invoke('create', 'Für Emma', ['music/Rock/02.flac'])
    assert created.id == 'fur-emma'
    assert (folder / 'fur-emma.m3u').read_text() == '#EXTM3U\n#PLAYLIST:Für Emma\nmusic/Rock/02.flac\n'
    assert [(e.title, e.artist) for e in created.entries] == [('Louder', 'Band')]

    playlists.invoke('add', 'fur-emma', ['music/Pop/01.flac', 'music/Rock/01.flac'])
    changed = playlists.invoke('save', 'fur-emma', 'Emmas Lieder',
                               ['music/Rock/01.flac', 'music/Rock/02.flac', 'music/Pop/01.flac'])
    assert (changed.id, changed.title) == ('fur-emma', 'Emmas Lieder')
    assert [e.title for e in changed.entries] == ['Loud', 'Louder', 'Sweet']
    [summary] = playlists.invoke('list_playlists')
    assert (summary.title, summary.tracks) == ('Emmas Lieder', 3)
    assert summary.duration == pytest.approx(0.3, abs=0.03)
    assert events[-1][0] == 'playlists.changed'

    assert playlists.invoke('create', 'Für Emma').id == 'fur-emma-2'
    playlists.invoke('delete', 'fur-emma')
    assert [p.id for p in playlists.invoke('list_playlists')] == ['fur-emma-2']


def test_play_skips_songs_no_longer_in_the_library(setup):
    manager, ctrl, folder, _ = setup
    playlists = manager.handle('playlists')
    playlists.invoke('create', 'Mix', ['music/Rock/01.flac', 'music/Rock/02.flac'])
    (folder / 'mix.m3u').write_text('#EXTM3U\n#PLAYLIST:Mix\nmusic/Gone.flac\nmusic/Rock/01.flac\nmusic/Rock/02.flac\n')
    assert [e.missing for e in playlists.invoke('get_playlist', 'mix').entries] == [True, False, False]
    playlists.invoke('play', 'mix', 2)
    ctrl.play_files.assert_called_once_with(['music/Rock/01.flac', 'music/Rock/02.flac'], 1, 0.0, False)
    ctrl.playerstatus.return_value = {'state': 'play', 'file': 'music/Rock/02.flac'}
    context = manager.handle('player').invoke('playerstatus').context
    assert (context.title, context.action, context.args) == ('Mix', 'playlists.play', {'playlist': 'mix'})


@pytest.mark.parametrize('files', [['../outside.flac'], ['music/Rock/cover.jpg'], ['/etc/passwd']])
def test_only_audio_files_of_the_library(setup, files):
    manager, _, _, _ = setup
    with pytest.raises(OperationError) as error:
        manager.handle('playlists').invoke('create', 'X', files)
    assert error.value.status == 422


@pytest.mark.parametrize('playlist, status', [('nope', 404), ('../x', 422), ('', 422)])
def test_unknown_or_invalid_playlists(setup, playlist, status):
    manager, _, _, _ = setup
    with pytest.raises(OperationError) as error:
        manager.handle('playlists').invoke('play', playlist)
    assert error.value.status == status
