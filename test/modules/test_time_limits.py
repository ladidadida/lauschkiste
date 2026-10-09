import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest

import lauschkiste.time_limits as module
from lauschkiste.time_limits import TimeLimits
from lauschkiste.time_limits.rules import limit_seconds, quiet_until

FRIDAY_EVENING = datetime(2026, 10, 9, 20, 0)       # a Friday
SATURDAY_MORNING = datetime(2026, 10, 10, 6, 30)
SATURDAY_NOON = datetime(2026, 10, 10, 12, 0)
MONDAY_NOON = datetime(2026, 10, 12, 12, 0)


def ranges(start='19:30', end='07:00', days='every day'):
    return {'bedtime': (start, end, days)}


def test_quiet_hours_across_midnight_belong_to_the_day_they_start_on():
    assert quiet_until(ranges(), FRIDAY_EVENING) == datetime(2026, 10, 10, 7, 0)
    assert quiet_until(ranges(), SATURDAY_MORNING) == datetime(2026, 10, 10, 7, 0)
    assert quiet_until(ranges(), SATURDAY_NOON) is None
    # weekdays only: Friday evening is covered (until Saturday 07:00), Saturday evening is not
    assert quiet_until(ranges(days='weekdays'), SATURDAY_MORNING) == datetime(2026, 10, 10, 7, 0)
    assert quiet_until(ranges(days='weekdays'), datetime(2026, 10, 10, 20, 0)) is None
    assert quiet_until(ranges(days='weekdays'), datetime(2026, 10, 12, 5, 0)) is None  # Monday morning: Sunday's
    assert quiet_until(ranges(days='weekends'), datetime(2026, 10, 10, 20, 0)) == datetime(2026, 10, 11, 7, 0)


def test_quiet_hours_within_a_day_and_the_end_is_free():
    school = {'school': ('08:00', '13:00', 'weekdays')}
    assert quiet_until(school, MONDAY_NOON) == datetime(2026, 10, 12, 13, 0)
    assert quiet_until(school, datetime(2026, 10, 12, 13, 0)) is None
    assert quiet_until(school, SATURDAY_NOON) is None


def test_the_limit_of_the_day():
    assert limit_seconds(120, None, MONDAY_NOON) == 7200
    assert limit_seconds(120, None, SATURDAY_NOON) == 7200
    assert limit_seconds(120, 180, SATURDAY_NOON) == 10800
    assert limit_seconds(120, 0, SATURDAY_NOON) is None
    assert limit_seconds(0, None, MONDAY_NOON) is None


class Setup:
    def __init__(self, tmp_path, config, now, clock=lambda: True):
        self.now = now
        self.plugin = TimeLimits(now=lambda: self.now, clock=clock)
        self.ctx = MagicMock()
        self.config = config
        self.ctx.config.get.side_effect = lambda key, default=None: self.config.get(key, default)
        self.plugin._ctx = self.ctx
        self.plugin._path = tmp_path / 'time_limits.json'

    def tick(self, seconds=1.0, playing=True):
        self.plugin._playing = playing
        self.plugin._tick(seconds, self.monotonic)
        self.monotonic += seconds

    monotonic = 1000.0


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'SETTLE_SEC', 0.0)

    def make(now=MONDAY_NOON, **config):
        defaults = {'enabled': True, 'quiet_hours': {'bedtime': {'start': '19:30', 'end': '07:00', 'days': 'every day'}},
                    'daily_limit_minutes': 1, 'weekend_limit_minutes': None, 'warn_minutes': 0, 'fade_seconds': 7}
        return Setup(tmp_path, {**defaults, **config}, now)
    return make


def test_the_playing_time_is_counted_and_the_limit_fades_out_once(setup):
    s = setup()
    for _ in range(59):
        s.tick()
    assert s.plugin.status().remaining_seconds == 1 and not s.plugin.status().blocked
    s.ctx.modules.volume.fade_out.assert_not_called()
    s.tick()
    s.tick()
    s.ctx.modules.volume.fade_out.assert_called_once_with(7.0)
    s.ctx.modules.player.stop.assert_not_called()
    status = s.plugin.status()
    assert status.blocked and status.reason == 'limit' and status.remaining_seconds == 0


def test_playback_started_after_the_limit_stops_at_once(setup):
    s = setup()
    s.plugin._state.update({'day': MONDAY_NOON.date().isoformat(), 'played': 60.0})
    s.tick(playing=False)
    s.tick(playing=True)
    s.ctx.modules.player.stop.assert_called_once()
    s.ctx.modules.volume.fade_out.assert_not_called()


def test_quiet_hours_stop_playback_and_the_morning_frees_it(setup):
    s = setup(now=FRIDAY_EVENING, daily_limit_minutes=0)
    s.tick(playing=False)
    s.tick(playing=True)
    s.ctx.modules.player.stop.assert_called_once()
    status = s.plugin.status()
    assert (status.blocked, status.reason, status.until) == (True, 'quiet', '07:00')
    s.now = SATURDAY_NOON
    assert not s.plugin.status().blocked


def test_a_clock_that_is_not_synchronized_does_not_enforce_quiet_hours(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'SETTLE_SEC', 0.0)
    s = Setup(tmp_path, {'enabled': True, 'quiet_hours': {'bedtime': {'start': '19:30', 'end': '07:00', 'days': 'every day'}},
                         'daily_limit_minutes': 0}, FRIDAY_EVENING, clock=lambda: False)
    s.tick()
    status = s.plugin.status()
    assert status.clock_ok is False and status.blocked is False
    s.ctx.modules.player.stop.assert_not_called()


def test_allow_adds_time_and_lifts_quiet_hours_for_that_long(setup):
    s = setup(now=FRIDAY_EVENING)
    assert s.plugin.status().blocked
    status = s.plugin.allow(10)
    assert status.blocked is False and status.extra_seconds == 600 and status.limit_seconds == 660
    s.plugin._state['allow_until'] = 0.0  # the ten minutes are over
    assert s.plugin.status().reason == 'quiet'
    status = s.plugin.reset_today()
    assert status.extra_seconds == 0 and status.played_seconds == 0


def test_a_new_day_starts_from_zero(setup):
    s = setup()
    for _ in range(30):
        s.tick()
    assert s.plugin.status().played_seconds == 30
    s.now = datetime(2026, 10, 13, 12, 0)
    assert s.plugin.status().played_seconds == 0


def test_the_warning_comes_once(setup):
    s = setup(daily_limit_minutes=2, warn_minutes=1, warning_sound='sounds/warn.wav')
    for _ in range(59):
        s.tick()
    s.ctx.modules.jingle.play.assert_not_called()
    for _ in range(5):
        s.tick()
    s.ctx.modules.jingle.play.assert_called_once_with('sounds/warn.wav')


def test_the_state_survives_a_restart(setup, tmp_path):
    s = setup()
    for _ in range(12):
        s.tick()
    s.plugin._save()
    saved = json.loads((tmp_path / 'time_limits.json').read_text())
    assert saved['day'] == '2026-10-12' and round(saved['played']) == 12


def test_switched_off_nothing_is_counted_or_blocked(setup):
    s = setup(enabled=False, daily_limit_minutes=1)
    for _ in range(90):
        s.tick()
    status = s.plugin.status()
    assert (status.enabled, status.blocked, status.played_seconds) == (False, False, 0)
    s.ctx.modules.volume.fade_out.assert_not_called()
    s.ctx.modules.player.stop.assert_not_called()
