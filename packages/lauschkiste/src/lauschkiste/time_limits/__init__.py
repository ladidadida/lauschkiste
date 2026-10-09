"""The time_limits core module: quiet hours and a daily listening limit.

It is off until switched on in the settings::

    time_limits:
      enabled: true
      quiet_hours:
        bedtime: {start: '19:30', end: '07:00', days: every day}
      daily_limit_minutes: 120

Playback that starts in quiet hours is stopped at once. The time something plays is counted per day; when the
limit is reached the sound fades out and the player stops, and playback stays blocked until the next day.
The action ``time_limits.allow`` adds time for today (and lifts quiet hours for that time); put it on a card
for the parents.
"""

import json
import logging
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Literal, Optional

from pydantic import BaseModel, Field

import lauschkiste.paths
from lauschkiste.contract import CoreModule, action, query
from lauschkiste.time_limits.rules import limit_seconds, quiet_until

logger = logging.getLogger('lauschkiste.time_limits')

STATE_FILE = 'settings/time_limits.json'
TICK_SEC = 1.0
SAVE_EVERY_SEC = 30.0
CLOCK_CHECK_SEC = 120.0
#: after stopping the player the rules are not applied again for this long (the status needs a moment to follow)
SETTLE_SEC = 3.0


class QuietHours(BaseModel):
    start: str = Field('19:30', title='From', pattern=r'^([01]?\d|2[0-3]):[0-5]\d$')
    end: str = Field('07:00', title='Until', pattern=r'^([01]?\d|2[0-3]):[0-5]\d$')
    days: Literal['every day', 'weekdays', 'weekends'] = Field('every day', title='On')


def default_quiet_hours() -> Dict[str, QuietHours]:
    return {'bedtime': QuietHours()}


class TimeLimitsSettings(BaseModel):
    enabled: bool = Field(False, title='Use time limits',
                          description='Quiet hours and the daily listening time below apply when this is on')
    quiet_hours: Dict[str, QuietHours] = Field(default_factory=default_quiet_hours, title='Quiet hours')
    daily_limit_minutes: int = Field(120, ge=0, le=1440, title='Listening time per day (minutes)',
                                     description='0: no limit')
    weekend_limit_minutes: Optional[int] = Field(None, ge=0, le=1440, title='Listening time on weekends (minutes)',
                                                 description='Empty: the same as on other days; 0: no limit')
    warn_minutes: int = Field(5, ge=0, le=60, title='Warn before the limit (minutes)', description='0: no warning')
    fade_seconds: int = Field(10, ge=1, le=120, title='Fade out over (seconds)')
    warning_sound: str = Field('', title='Sound for the warning', description='A file in the home directory; empty: none')
    blocked_sound: str = Field('', title='Sound when playback is blocked',
                               description='A file in the home directory; empty: none')


class TimeLimitStatus(BaseModel):
    #: false while the time limits are switched off; nothing is blocked or counted then
    enabled: bool = True
    #: false when the system clock is not synchronized: quiet hours are not enforced then
    clock_ok: bool
    blocked: bool
    #: 'quiet' (quiet hours) or 'limit' (the day's time is used up)
    reason: Optional[str] = None
    #: for quiet hours, when they end ("07:00")
    until: Optional[str] = None
    played_seconds: int
    limit_seconds: Optional[int] = None
    remaining_seconds: Optional[int] = None
    extra_seconds: int = 0


def clock_synchronized() -> Optional[bool]:
    """Whether the clock is synchronized (None if the system cannot tell)."""
    try:
        result = subprocess.run(['timedatectl', 'show', '-p', 'NTPSynchronized', '--value'], capture_output=True,
                                text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip().lower()
    return value == 'yes' if value in ('yes', 'no') else None


class TimeLimits(CoreModule):
    """Quiet hours and a daily listening limit (off until switched on)."""

    name = 'time_limits'
    interface_version = '1.0'
    requires = ('player', 'volume', 'jingle')
    settings = TimeLimitsSettings

    def __init__(self, now: Callable[[], datetime] = datetime.now, clock: Callable[[], Optional[bool]] = clock_synchronized):
        self._now = now
        self._clock = clock
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {'day': '', 'played': 0.0, 'extra': 0, 'allow_until': 0.0, 'warned': False}
        self._path = Path(STATE_FILE)
        self._playing = False
        self._fading = False
        self._was_blocked = False
        self._settle_until = 0.0
        self._clock_ok = True
        self._clock_checked = float('-inf')
        self._saved_at = 0.0
        self._stopped = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # -- lifecycle ------------------------------------------------------------------------------

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._path = lauschkiste.paths.resolve(STATE_FILE)
        try:
            saved = json.loads(self._path.read_text())
            if isinstance(saved, dict):
                self._state.update({k: saved[k] for k in self._state if k in saved})
        except (OSError, ValueError):
            pass
        ctx.subscribe('player.status', self._on_status)
        self._thread = threading.Thread(target=self._run, name='time-limits', daemon=True)
        self._thread.start()

    def stop(self):
        self._stopped.set()
        self._save()
        return []

    def settings_changed(self, changed) -> bool:
        return True

    # -- the state of the day -------------------------------------------------------------------

    def _roll_over(self, now: datetime) -> None:
        day = now.date().isoformat()
        if self._state['day'] != day:
            self._state.update({'day': day, 'played': 0.0, 'extra': 0, 'allow_until': 0.0, 'warned': False})

    def _save(self) -> None:
        with self._lock:
            data = dict(self._state)
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(data))
        except OSError as error:
            logger.warning(f"Could not save the listening time: {error}")

    def _ranges(self) -> Dict[str, tuple]:
        entries = self._ctx.config.get('quiet_hours', default=None)
        if not isinstance(entries, dict):
            entries = {key: value.model_dump() for key, value in default_quiet_hours().items()}
        ranges = {}
        for key, values in entries.items():
            try:
                parsed = QuietHours(**dict(values or {}))
            except Exception:
                logger.warning(f"Ignoring the quiet hours '{key}': not valid")
                continue
            ranges[key] = (parsed.start, parsed.end, parsed.days)
        return ranges

    def _limit(self, now: datetime) -> Optional[int]:
        weekend = self._ctx.config.get('weekend_limit_minutes', default=None)
        return limit_seconds(int(self._ctx.config.get('daily_limit_minutes', default=120)),
                             None if weekend is None else int(weekend), now)

    def _clock_is_ok(self) -> bool:
        if time.monotonic() - self._clock_checked >= CLOCK_CHECK_SEC:
            self._clock_checked = time.monotonic()
            self._clock_ok = self._clock() is not False
        return self._clock_ok

    def _enabled(self) -> bool:
        return bool(self._ctx.config.get('enabled', default=False))

    def evaluate(self) -> TimeLimitStatus:
        """Where the day stands (called by the tick, the status query and the actions)."""
        now = self._now()
        if not self._enabled():
            return TimeLimitStatus(enabled=False, clock_ok=True, blocked=False, played_seconds=0)
        with self._lock:
            self._roll_over(now)
            state = dict(self._state)
        clock_ok = self._clock_is_ok()
        limit = self._limit(now)
        extra = int(state['extra'])
        played = int(state['played'])
        reason, until = None, None
        allowed = time.time() < float(state['allow_until'])
        if clock_ok and not allowed:
            end = quiet_until(self._ranges(), now)
            if end is not None:
                reason, until = 'quiet', end.strftime('%H:%M')
        if reason is None and limit is not None and played >= limit + extra:
            reason = 'limit'
        remaining = None if limit is None else max(0, limit + extra - played)
        return TimeLimitStatus(clock_ok=clock_ok, blocked=reason is not None, reason=reason, until=until,
                               played_seconds=played, limit_seconds=None if limit is None else limit + extra,
                               remaining_seconds=remaining, extra_seconds=extra)

    # -- keeping the rules ----------------------------------------------------------------------

    def _on_status(self, _topic, status) -> None:
        self._playing = bool(status) and status.get('state') == 'play'
        if not self._playing:
            self._fading = False

    def _run(self) -> None:
        last = time.monotonic()
        while not self._stopped.wait(TICK_SEC):
            now_monotonic = time.monotonic()
            elapsed, last = now_monotonic - last, now_monotonic
            try:
                self._tick(elapsed, now_monotonic)
            except Exception:
                logger.exception("The time limits could not be checked")

    def _tick(self, elapsed: float, now_monotonic: float) -> None:
        if not self._enabled():
            self._was_blocked = False
            return
        with self._lock:
            self._roll_over(self._now())
            if self._playing and not self._fading:
                self._state['played'] = float(self._state['played']) + elapsed
        status = self.evaluate()
        crossed = status.blocked and not self._was_blocked and self._playing
        self._was_blocked = status.blocked
        if now_monotonic - self._saved_at >= SAVE_EVERY_SEC:
            self._saved_at = now_monotonic
            self._save()
        if not self._playing or self._fading or now_monotonic < self._settle_until:
            return
        if status.blocked:
            self._enforce(status, now_monotonic, crossed)
        elif status.remaining_seconds is not None:
            self._warn(status)

    def _sound(self, name: str) -> None:
        sound = str(self._ctx.config.get(name, default='') or '')
        if sound:
            try:
                self._ctx.modules.jingle.play(sound)
            except Exception as error:
                logger.warning(f"Could not play '{sound}': {error}")

    def _enforce(self, status: TimeLimitStatus, now_monotonic: float, crossed: bool) -> None:
        """Stop what plays. The limit being reached during playback fades out; playback started while blocked stops."""
        if status.reason == 'limit' and crossed:
            self._fading = True
            logger.info("The listening time of the day is used up: fading out")
            self._ctx.modules.volume.fade_out(float(self._ctx.config.get('fade_seconds', default=10)))
        else:
            logger.info(f"Playback is blocked ({status.reason}): stopping")
            self._ctx.modules.player.stop()
            self._sound('blocked_sound')
        self._settle_until = now_monotonic + SETTLE_SEC

    def _warn(self, status: TimeLimitStatus) -> None:
        warn = int(self._ctx.config.get('warn_minutes', default=5)) * 60
        if not warn or status.remaining_seconds is None or status.remaining_seconds > warn:
            return
        with self._lock:
            if self._state['warned']:
                return
            self._state['warned'] = True
        self._sound('warning_sound')

    # -- operations -----------------------------------------------------------------------------

    @query(path='/status')
    def status(self) -> TimeLimitStatus:
        """Quiet hours, the time used today and what is left."""
        return self.evaluate()

    @action()
    def allow(self, minutes: int = 30) -> TimeLimitStatus:
        """Add listening time for today; quiet hours are lifted for that long as well. Meant for parents (put it on a card)."""
        minutes = max(1, min(int(minutes), 600))
        with self._lock:
            self._roll_over(self._now())
            self._state['extra'] = int(self._state['extra']) + minutes * 60
            self._state['allow_until'] = max(time.time(), float(self._state['allow_until'])) + minutes * 60
            self._state['warned'] = False
        self._settle_until = 0.0
        self._save()
        return self.evaluate()

    @action()
    def reset_today(self) -> TimeLimitStatus:
        """Count today's listening time from zero again."""
        with self._lock:
            self._state.update({'played': 0.0, 'extra': 0, 'allow_until': 0.0, 'warned': False})
        self._save()
        return self.evaluate()
