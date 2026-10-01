import pytest

from lauschkiste.legacy_actions import convert, is_legacy

PARAMS = {
    'player.play_folder': ['folder', 'recursive'],
    'player.next': [],
    'timers.start': ['timer', 'wait_seconds'],
    'volume.set_volume': ['volume'],
}


def names(action_id):
    return PARAMS.get(action_id)


@pytest.mark.parametrize('entry, expected', [
    ({'alias': 'play_folder', 'args': ['Rock']}, {'action': 'player.play_folder', 'args': {'folder': 'Rock'}}),
    ({'alias': 'play_folder', 'args': 'Rock'}, {'action': 'player.play_folder', 'args': {'folder': 'Rock'}}),
    ({'alias': 'play_folder', 'kwargs': {'folder': 'Rock', 'recursive': True}},
     {'action': 'player.play_folder', 'args': {'folder': 'Rock', 'recursive': True}}),
    ({'alias': 'next_song'}, {'action': 'player.next', 'args': {}}),
    ({'alias': None}, {'action': 'system.noop', 'args': {}}),
    ({'package': 'player', 'plugin': 'ctrl', 'method': 'next'}, {'action': 'player.next', 'args': {}}),
    ({'package': 'volume', 'plugin': 'ctrl', 'method': 'set_volume', 'args': [12]},
     {'action': 'volume.set_volume', 'args': {'volume': 12}}),
    ({'package': 'host', 'plugin': 'shutdown'}, {'action': 'raspberry_pi.shutdown', 'args': {}}),
    ({'package': 'misc', 'plugin': 'empty_rpc_call'}, {'action': 'system.noop', 'args': {}}),
    ({'alias': 'timer_shutdown', 'args': [600]},
     {'action': 'timers.start', 'args': {'timer': 'shutdown', 'wait_seconds': 600}}),
    ({'package': 'timers', 'plugin': 'timer_stop_player', 'method': 'cancel'},
     {'action': 'timers.cancel', 'args': {'timer': 'stop_player'}}),
    ({'alias': 'toggle', 'ignore_same_id_delay': True},
     {'action': 'player.toggle', 'args': {}, 'ignore_same_id_delay': True}),
    ({'action': 'player.next', 'ignore_card_removal_action': True},
     {'action': 'player.next', 'args': {}, 'ignore_card_removal_action': True}),
])
def test_convert(entry, expected):
    assert convert(entry, names) == (expected, None)


@pytest.mark.parametrize('entry, problem', [
    ({'alias': 'nonsense'}, 'unknown alias'),
    ({'alias': 'change_volume', 'args': [5]}, "can't be named"),
    ({'alias': 'play_folder', 'args': ['a', True, 'extra']}, 'too many'),
    ({'plugin': 'ctrl'}, "neither"),
    ({'alias': 'play_folder', 'kwargs': ['x']}, 'mapping'),
])
def test_convert_problems(entry, problem):
    converted, reason = convert(entry, names)
    assert converted is None
    assert problem in reason


def test_is_legacy():
    assert is_legacy({'alias': 'play'})
    assert is_legacy({'package': 'player'})
    assert not is_legacy({'action': 'player.play'})
