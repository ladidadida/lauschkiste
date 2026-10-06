"""The timers core module: named countdowns that run an action when they expire.

Timers are configured under ``timers:``; each runs an action (``action``/``args``) after
``default_timeout_sec`` unless started with another duration. A timer whose action is not available
(e.g. its plugin is disabled) is listed, but can't be started.
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from lauschkiste.contract import ActionError, CoreModule, OperationError, action, event, query

logger = logging.getLogger('lauschkiste.timers')

DEFAULT_TIMERS: Dict[str, Dict[str, Any]] = {
    'stop_player': {'action': 'player.stop', 'default_timeout_sec': 3600},
    'fade_volume': {'action': 'volume.fade_out', 'args': {'seconds': 30}, 'default_timeout_sec': 600},
    'shutdown': {'action': 'hardware.shutdown', 'default_timeout_sec': 3600},
}


class TimerState(BaseModel):
    name: str
    action: str
    args: Dict[str, Any] = {}
    available: bool
    enabled: bool
    wait_seconds: float
    remaining_seconds: float


class _Timer:
    def __init__(self, name: str, action_id: str, args: Dict[str, Any], default_timeout: float):
        self.name = name
        self.action = action_id
        self.args = args
        self.wait_seconds = default_timeout
        self.deadline: Optional[float] = None
        self.thread: Optional[threading.Timer] = None

    def remaining(self) -> float:
        return 0.0 if self.deadline is None else max(0.0, self.deadline - time.monotonic())


class Timers(CoreModule):
    """Countdown timers that run an action when they expire."""

    name = 'timers'
    interface_version = '1.0'

    changed = event('changed', TimerState)

    def __init__(self):
        self._ctx = None
        self._timers: Dict[str, _Timer] = {}

    def start(self, ctx) -> None:
        self._ctx = ctx
        configured = {name: dict(values) for name, values in DEFAULT_TIMERS.items()}
        for name, values in (ctx.config.as_dict() or {}).items():
            if isinstance(values, dict):
                configured.setdefault(name, {}).update(values)
        for name, values in configured.items():
            if not values.get('action'):
                continue
            self._timers[name] = _Timer(name, values['action'], dict(values.get('args') or {}),
                                        float(values.get('default_timeout_sec', 3600)))

    def ready(self) -> None:
        for timer in self._timers.values():
            self._publish(timer)

    def stop(self):
        for timer in self._timers.values():
            if timer.thread is not None:
                timer.thread.cancel()
        return []

    def _available(self, timer: _Timer) -> bool:
        try:
            self._ctx.actions.validate(timer.action, timer.args)
        except ActionError:
            return False
        return True

    def _state(self, timer: _Timer) -> TimerState:
        return TimerState(name=timer.name, action=timer.action, args=timer.args, available=self._available(timer),
                          enabled=timer.deadline is not None, wait_seconds=timer.wait_seconds,
                          remaining_seconds=round(timer.remaining(), 1))

    def _publish(self, timer: _Timer) -> TimerState:
        state = self._state(timer)
        self._ctx.publish(self.changed, state)
        return state

    def _get(self, name: str) -> _Timer:
        try:
            return self._timers[name]
        except KeyError:
            raise OperationError(404, 'unknown_timer',
                                 f"Unknown timer '{name}'. Available: {sorted(self._timers)}") from None

    def _expire(self, timer: _Timer, deadline: float) -> None:
        with self._ctx.lock:
            if timer.deadline != deadline:
                return
            timer.deadline = None
            timer.thread = None
            self._publish(timer)
        logger.info(f"Timer '{timer.name}' expired, running '{timer.action}'")
        self._ctx.actions.call_ignore_errors(timer.action, timer.args)

    # -- operations -----------------------------------------------------------------------------

    @query(path='')
    def list_timers(self) -> List[TimerState]:
        """All timers with their state."""
        return [self._state(timer) for timer in self._timers.values()]

    @action(name='start', path='/start')
    def start_timer(self, timer: str, wait_seconds: Optional[float] = None) -> TimerState:
        """Start (or restart) a timer; ``wait_seconds`` defaults to the timer's configured timeout."""
        entry = self._get(timer)
        if not self._available(entry):
            raise OperationError(409, 'timer_unavailable',
                                 f"Timer '{timer}' runs '{entry.action}', which is not available")
        if wait_seconds is not None:
            if wait_seconds <= 0:
                raise OperationError(422, 'invalid_timeout', 'wait_seconds must be positive')
            entry.wait_seconds = float(wait_seconds)
        if entry.thread is not None:
            entry.thread.cancel()
        deadline = time.monotonic() + entry.wait_seconds
        entry.deadline = deadline
        entry.thread = threading.Timer(entry.wait_seconds, self._expire, args=(entry, deadline))
        entry.thread.name = f'timer.{timer}'
        entry.thread.daemon = True
        entry.thread.start()
        logger.info(f"Timer '{timer}' started: '{entry.action}' in {entry.wait_seconds:.0f}s")
        return self._publish(entry)

    @action(path='/cancel')
    def cancel(self, timer: str) -> TimerState:
        """Cancel a running timer."""
        entry = self._get(timer)
        if entry.thread is not None:
            entry.thread.cancel()
        entry.thread = None
        entry.deadline = None
        return self._publish(entry)

    @action(path='/toggle')
    def toggle(self, timer: str, wait_seconds: Optional[float] = None) -> TimerState:
        """Start the timer if it is not running, cancel it otherwise."""
        entry = self._get(timer)
        if entry.deadline is not None:
            return self.cancel(timer)
        return self.start_timer(timer, wait_seconds)
