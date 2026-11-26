import json
from concurrent.futures import Future
from unittest.mock import Mock

import pytest

from lauschkiste.player.module import Player
from lauschkiste.player.status import PlaybackContext, PlayerStatus


class InlineExecutor:
    def submit(self, func, *args):
        future = Future()
        future.set_result(func(*args))
        return future


@pytest.fixture
def player(tmp_path):
    player = Player()
    player._ctx = Mock()
    player._coordinator = Mock()
    player._coordinator.playerstatus.return_value = {'state': 'stop'}
    player._coordinator.playlistinfo.return_value = []
    player._session_path = tmp_path / 'player_session.json'
    player._session_worker = InlineExecutor()
    return player


def saved(player):
    return json.loads(player._session_path.read_text())


def test_what_plays_is_saved_when_it_changes(player):
    player._session_restored = True
    player._coordinator.playlistinfo.return_value = [{'file': '/lib/a.mp3'}, {'file': '/lib/b.mp3'}]
    player.play_files(['a.mp3', 'b.mp3'], context=PlaybackContext(kind='music', title='Mix', action='playlists.play',
                                                                  args={'playlist': 'mix'}))
    status = PlayerStatus(provider='local_audio', state='play', file='/lib/b.mp3', position=1, elapsed=12.0,
                          context=player._context)
    player._note_session(status)
    assert saved(player) == {'context': player._context.model_dump(mode='json'), 'files': ['/lib/a.mp3', '/lib/b.mp3'],
                             'index': 1, 'elapsed': 12.0, 'ordered': False}

    player._note_session(status.model_copy(update={'elapsed': 20.0}))
    assert saved(player)['elapsed'] == 12.0
    player._note_session(status.model_copy(update={'state': 'pause', 'elapsed': 21.0}))
    assert saved(player)['elapsed'] == 21.0


def test_nothing_is_saved_before_the_session_is_restored(player):
    player._note_session(PlayerStatus(provider='local_audio', state='stop'))
    assert not player._session_path.exists()


def test_music_is_loaded_paused_where_it_was(player):
    context = {'kind': 'music', 'title': 'Mix', 'action': 'playlists.play', 'args': {'playlist': 'mix'}}
    player._session = {'context': context, 'files': ['/lib/a.mp3', '/lib/b.mp3'], 'index': 1, 'elapsed': 12.0,
                       'ordered': False}
    player._restore_session()
    player._coordinator.load_files.assert_called_once_with(['/lib/a.mp3', '/lib/b.mp3'], 1, 12.0, False)
    player._coordinator.play_files.assert_not_called()
    assert player._context.title == 'Mix'
    assert player._session_restored

    player.play_files(['c.mp3'])
    player._coordinator.play_files.assert_called_once_with(['c.mp3'], 0, 0.0, False)


def test_an_audiobook_is_loaded_through_its_action(player):
    context = {'kind': 'audiobook', 'title': 'Pippi', 'action': 'audiobooks.play', 'args': {'book': 'Pippi'}}
    player._session = {'context': context, 'files': ['/lib/p/1.mp3'], 'index': 0, 'elapsed': 3.0, 'ordered': True}

    def play_book(action, args):
        player.play_files(['p/1.mp3'], 0, 40.0, True, context)
    player._ctx.actions.call.side_effect = play_book

    player._restore_session()
    player._ctx.actions.call.assert_called_once_with('audiobooks.play', {'book': 'Pippi'})
    player._coordinator.load_files.assert_called_once_with(['p/1.mp3'], 0, 40.0, True)
    player._coordinator.play_files.assert_not_called()


def test_a_radio_station_is_loaded_from_its_start(player):
    context = {'kind': 'radio', 'title': 'FM', 'action': 'radio.play', 'args': {'station': 'fm'}}
    player._session = {'context': context, 'files': ['https://fm/stream'], 'index': 0, 'elapsed': 3600.0}
    player._restore_session()
    player._coordinator.load_files.assert_called_once_with(['https://fm/stream'], 0, 0.0, False)


def test_nothing_is_loaded_when_something_plays_already_or_loading_fails(player):
    player._session = {'files': ['/lib/a.mp3']}
    player._coordinator.playerstatus.return_value = {'state': 'play'}
    player._restore_session()
    player._coordinator.load_files.assert_not_called()

    player._session = {'files': ['/lib/a.mp3']}
    player._coordinator.playerstatus.return_value = {'state': 'stop'}
    player._coordinator.load_files.side_effect = NotImplementedError
    player._restore_session()
    assert player._session_restored and player._loading_thread is None
