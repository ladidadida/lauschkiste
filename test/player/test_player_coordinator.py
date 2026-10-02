from types import SimpleNamespace
from unittest.mock import Mock, call, sentinel

import pytest

from lauschkiste.player.coordinator import PlayerCoordinator


def backend_with(**methods):
    defaults = {
        'stop': Mock(),
        'exit': Mock(),
    }
    defaults.update(methods)
    return SimpleNamespace(**defaults)


def test_registers_and_selects_first_backend():
    coordinator = PlayerCoordinator()
    mpd_backend = backend_with()
    other_backend = backend_with()

    coordinator.register_backend('mpd', mpd_backend)
    coordinator.register_backend('other', other_backend)

    assert coordinator.list_backends() == ['mpd', 'other']
    assert coordinator.get_active_backend() == 'mpd'
    assert coordinator.get_default_backend() == 'mpd'
    mpd_backend.stop.assert_not_called()


def test_rejects_invalid_backend_registrations():
    coordinator = PlayerCoordinator()
    coordinator.register_backend('mpd', backend_with())

    with pytest.raises(ValueError, match="must not be empty"):
        coordinator.register_backend('', backend_with())
    with pytest.raises(ValueError, match="already registered"):
        coordinator.register_backend('mpd', backend_with())


@pytest.mark.parametrize(
    ('coordinator_method', 'call_args', 'backend_args'),
    [
        ('get_player_type_and_version', (), ()),
        ('update', (), ()),
        ('update_wait', (), ()),
        ('play', (), ()),
        ('stop', (), ()),
        ('pause', (), (1,)),
        ('pause', (0,), (0,)),
        ('prev', (), ()),
        ('next', (), ()),
        ('seek', (23,), (23,)),
        ('rewind', (), ()),
        ('replay', (), ()),
        ('toggle', (), ()),
        ('replay_if_stopped', (), ()),
        ('shuffle', (), ('toggle',)),
        ('shuffle', ('enable',), ('enable',)),
        ('repeat', (), ('toggle',)),
        ('repeat', ('disable',), ('disable',)),
        ('get_current_song', ('title',), ('title',)),
        ('map_filename_to_playlist_pos', ('song.mp3',), ('song.mp3',)),
        ('remove', (), ()),
        ('move', (), ()),
        ('play_single', ('album/song.mp3',), ('album/song.mp3',)),
        ('resume', (), ()),
        ('play_folder', ('album',), ('album', False)),
        ('play_folder', ('album', True), ('album', True)),
        ('play_album', ('Artist', 'Album'), ('Artist', 'Album')),
        ('play_files', (['a.mp3', 'b.mp3'],), (['a.mp3', 'b.mp3'],)),
        ('queue_load', ('album',), ('album',)),
        ('playerstatus', (), ()),
        ('playlistinfo', (), ()),
        ('get_volume', (), ()),
        ('set_volume', (42,), (42,)),
    ],
)
def test_delegates_existing_player_contract(
        coordinator_method, call_args, backend_args):
    backend_method = Mock(return_value=sentinel.result)
    backend = backend_with(**{coordinator_method: backend_method})
    coordinator = PlayerCoordinator()
    coordinator.register_backend('mpd', backend)

    result = getattr(coordinator, coordinator_method)(*call_args)

    assert result is sentinel.result
    backend_method.assert_called_once_with(*backend_args)


def test_switch_stops_old_backend_before_new_content_starts():
    events = []
    mpd_backend = backend_with(stop=Mock(side_effect=lambda: events.append('mpd.stop')))
    streaming_backend = backend_with(
        play_single=Mock(side_effect=lambda content: events.append(f'play:{content}'))
    )
    coordinator = PlayerCoordinator()
    coordinator.register_backend('mpd', mpd_backend)
    coordinator.register_backend('streaming', streaming_backend)

    coordinator.play_single('service:track:123', provider='streaming')

    assert events == ['mpd.stop', 'play:service:track:123']
    assert coordinator.get_active_backend() == 'streaming'


def test_switch_updates_optional_backend_activation_state():
    local_backend = backend_with(set_active=Mock())
    streaming_backend = backend_with(set_active=Mock())
    coordinator = PlayerCoordinator()

    coordinator.register_backend('local', local_backend)
    coordinator.register_backend('streaming', streaming_backend)
    coordinator.select_backend('streaming')

    local_backend.set_active.assert_has_calls([call(True), call(False)])
    streaming_backend.set_active.assert_called_once_with(True)


def test_provider_qualified_content_selects_matching_backend():
    events = []
    local_backend = backend_with(
        stop=Mock(side_effect=lambda: events.append('local.stop')),
    )
    streaming_backend = backend_with(
        play_album=Mock(
            side_effect=lambda artist, album, uri: events.append(f'play:{uri}')
        ),
    )
    coordinator = PlayerCoordinator()
    coordinator.register_backend('local', local_backend)
    coordinator.register_backend('streaming', streaming_backend)

    coordinator.play_album(
        'Artist',
        'Album',
        content_uri='service:album:123',
        provider='streaming',
    )

    assert events == ['local.stop', 'play:service:album:123']
    assert coordinator.get_active_backend() == 'streaming'


def test_unqualified_content_switches_back_to_default_backend():
    local_backend = backend_with(play_single=Mock())
    streaming_backend = backend_with()
    coordinator = PlayerCoordinator()
    coordinator.register_backend('local', local_backend)
    coordinator.register_backend('streaming', streaming_backend)
    coordinator.select_backend('streaming')

    coordinator.play_single('Stories/Chapter 1: Arrival.mp3')

    streaming_backend.stop.assert_called_once_with()
    local_backend.play_single.assert_called_once_with(
        'Stories/Chapter 1: Arrival.mp3'
    )
    assert coordinator.get_active_backend() == 'local'


def test_selecting_active_backend_does_not_stop_it():
    backend = backend_with()
    coordinator = PlayerCoordinator()
    coordinator.register_backend('mpd', backend)

    assert coordinator.select_backend('mpd') == 'mpd'

    backend.stop.assert_not_called()


def test_unknown_backend_and_unsupported_operation_errors_are_clear():
    coordinator = PlayerCoordinator()
    coordinator.register_backend('mpd', backend_with())

    with pytest.raises(KeyError, match="Unknown player backend 'missing'"):
        coordinator.select_backend('missing')
    with pytest.raises(NotImplementedError, match="does not support 'play'"):
        coordinator.play()


def test_plain_folder_content_routes_to_mpd_backend():
    play_folder = Mock(return_value=sentinel.playback)
    coordinator = PlayerCoordinator()
    coordinator.register_backend('mpd', backend_with(play_folder=play_folder))

    result = coordinator.play_folder('stories/chapter-one')

    assert result is sentinel.playback
    play_folder.assert_called_once_with('stories/chapter-one', False)


def test_folder_content_switches_back_to_default_backend():
    local_backend = backend_with(play_folder=Mock())
    streaming_backend = backend_with()
    coordinator = PlayerCoordinator()
    coordinator.register_backend('local', local_backend)
    coordinator.register_backend('streaming', streaming_backend)
    coordinator.select_backend('streaming')

    coordinator.play_folder('stories')

    streaming_backend.stop.assert_called_once_with()
    local_backend.play_folder.assert_called_once_with('stories', False)
    assert coordinator.get_active_backend() == 'local'


@pytest.mark.parametrize('is_second_swipe', [False, True])
def test_play_card_runs_folder_or_second_swipe(is_second_swipe):
    backend = backend_with(is_second_swipe=Mock(return_value=is_second_swipe), play_folder=Mock(),
                           play_second_swipe=Mock())
    coordinator = PlayerCoordinator()
    coordinator.register_backend('mpd', backend)

    coordinator.play_card('stories', recursive=True)

    backend.is_second_swipe.assert_called_once_with('stories')
    if is_second_swipe:
        backend.play_folder.assert_not_called()
        backend.play_second_swipe.assert_called_once_with()
    else:
        backend.play_folder.assert_called_once_with('stories', True)
        backend.play_second_swipe.assert_not_called()


def test_configured_second_swipe_action_replaces_the_backend_behavior():
    override = Mock()
    backend = backend_with(is_second_swipe=Mock(return_value=True), play_second_swipe=Mock())
    coordinator = PlayerCoordinator(second_swipe_action=override)
    coordinator.register_backend('mpd', backend)

    coordinator.play_card('stories')

    override.assert_called_once_with()
    backend.play_second_swipe.assert_not_called()


def test_play_second_swipe_ignores_action_return_value():
    # play_second_swipe() is shared shape across backends (see e.g. PlayerMPD/PlayerLocalAudio):
    # it always returns None, regardless of what the configured second_swipe_action returns.
    class FakeBackend:
        def play_second_swipe(self):
            self.second_swipe_action()

    backend = FakeBackend()
    backend.second_swipe_action = Mock(return_value=sentinel.result)

    assert backend.play_second_swipe() is None
    backend.second_swipe_action.assert_called_once_with()


def test_playerstatus_is_returned_without_translation():
    player_status = {
        'state': 'play',
        'songid': '4',
        'title': 'Story',
        'artist': 'Reader',
        'album': 'Collection',
        'file': 'stories/story.mp3',
        'elapsed': '12.5',
        'duration': '60.0',
        'random': '0',
        'repeat': '0',
        'single': '0',
    }
    coordinator = PlayerCoordinator()
    coordinator.register_backend(
        'mpd', backend_with(playerstatus=Mock(return_value=player_status))
    )

    assert coordinator.playerstatus() is player_status


def test_exit_closes_all_backends_in_reverse_registration_order():
    first = backend_with(exit=Mock(return_value=sentinel.first))
    second = backend_with(exit=Mock(return_value=sentinel.second))
    coordinator = PlayerCoordinator()
    coordinator.register_backend('first', first)
    coordinator.register_backend('second', second)

    assert coordinator.exit() == [sentinel.second, sentinel.first]
