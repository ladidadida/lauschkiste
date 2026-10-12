"""The display core module: switches the backlight of the box's screen off after a time without a touch.

While the screen sleeps its touch screen is grabbed, so the touch that wakes it up never reaches the web app.
Screens without a controllable backlight (most HDMI monitors) are left alone.
"""

import logging
import select
import threading
import time
from pathlib import Path
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from lauschkiste.contract import CoreModule, action, query

logger = logging.getLogger('lauschkiste.display')

BACKLIGHT_ROOT = Path('/sys/class/backlight')
RESCAN_INTERVAL = 3.0
POLL_INTERVAL = 0.5
RELEASE_TIMEOUT = 2.0


class DisplaySettings(BaseModel):
    screen_off_minutes: int = Field(5, ge=0, le=1440, title='Switch the screen off after (minutes)',
                                    description='Minutes without a touch until the screen goes dark; a touch wakes '
                                                'it. 0 keeps it on. Only for screens with a controllable backlight.')


class DisplayState(BaseModel):
    available: bool
    asleep: bool


class Backlight:
    """The first backlight of the system that this process may write."""

    def __init__(self, root: Path = BACKLIGHT_ROOT):
        self._brightness: Optional[Path] = None
        self._saved: Optional[int] = None
        for directory in sorted(root.glob('*')):
            brightness = directory / 'brightness'
            try:
                with brightness.open('r+'):
                    pass
                self._max = int((directory / 'max_brightness').read_text())
            except (OSError, ValueError):
                continue
            self._brightness = brightness
            break

    @property
    def available(self) -> bool:
        return self._brightness is not None

    def off(self) -> None:
        if self._saved is None:
            level = int(self._brightness.read_text())
            self._saved = level or self._max
        self._brightness.write_text('0')

    def on(self) -> None:
        if self._saved is not None:
            self._brightness.write_text(str(self._saved))
            self._saved = None


class Evdev:
    """Access to the evdev library; replaced in tests."""

    def __init__(self):
        import evdev
        self._evdev = evdev

    def touch_screens(self) -> List[Any]:
        ecodes = self._evdev.ecodes
        screens = []
        for path in self._evdev.list_devices():
            try:
                device = self._evdev.InputDevice(path)
                capabilities = device.capabilities()
            except OSError:
                continue
            if ecodes.EV_ABS in capabilities and ecodes.BTN_TOUCH in capabilities.get(ecodes.EV_KEY, []):
                screens.append(device)
            else:
                device.close()
        return screens

    def read(self, devices: List[Any], timeout: float):
        """Wait for news; returns ``([(is_touch, pressed), ...], [lost devices])``."""
        touches, lost = [], []
        try:
            readable, _, _ = select.select(devices, [], [], timeout)
        except (OSError, ValueError):
            return touches, list(devices)
        for device in readable:
            try:
                touches.extend((event.type == self._evdev.ecodes.EV_KEY and event.code == self._evdev.ecodes.BTN_TOUCH,
                                event.value == 1) for event in device.read())
            except OSError:
                lost.append(device)
        return touches, lost


class Display(CoreModule):
    """Switches the screen off when nobody touches it."""

    name = 'display'
    interface_version = '1.0'
    concurrency = 'threadsafe'
    settings = DisplaySettings

    def __init__(self, backlight: Optional[Backlight] = None, evdev_access=None):
        self._backlight = backlight
        self._evdev_factory = evdev_access or Evdev
        self._ctx = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._asleep = False
        self._last_touch = time.monotonic()
        self._release_deadline: Optional[float] = None
        self._screens: List[Any] = []

    def start(self, ctx) -> None:
        self._ctx = ctx
        if self._backlight is None:
            self._backlight = Backlight()
        if not self._backlight.available:
            logger.info("No controllable screen backlight, the screen is never switched off")
            return
        try:
            self._evdev = self._evdev_factory()
        except ImportError as error:
            logger.error(f"Switching the screen off needs evdev: {error}")
            return
        self._thread = threading.Thread(target=self._run, name='display', daemon=True)
        self._thread.start()

    def settings_changed(self, changed) -> bool:
        return True

    def stop(self) -> List[threading.Thread]:
        self._stop.set()
        return [self._thread] if self._thread else []

    # -- watching -------------------------------------------------------------------------------

    def _run(self) -> None:
        next_scan = 0.0
        try:
            while not self._stop.is_set():
                if time.monotonic() >= next_scan:
                    self._rescan()
                    next_scan = time.monotonic() + RESCAN_INTERVAL
                self._poll()
                self._check_idle()
        except Exception:
            logger.exception("Watching the touch screen failed")
        finally:
            self._wake()
            for device in self._screens:
                device.close()

    def _rescan(self) -> None:
        known = {device.path for device in self._screens}
        for device in self._evdev.touch_screens():
            if device.path in known:
                device.close()
                continue
            self._screens.append(device)
            if self._asleep:
                device.grab()

    def _poll(self) -> None:
        if not self._screens:
            self._stop.wait(POLL_INTERVAL)
            return
        touches, lost = self._evdev.read(self._screens, POLL_INTERVAL)
        for device in lost:
            self._screens.remove(device)
            device.close()
        for is_touch, pressed in touches:
            self._touched(is_touch, pressed)

    def _touched(self, is_touch: bool, pressed: bool) -> None:
        with self._lock:
            self._last_touch = time.monotonic()
            if not self._asleep:
                return
            if is_touch and pressed:
                self._backlight.on()
                self._release_deadline = time.monotonic() + RELEASE_TIMEOUT
            elif is_touch and self._release_deadline is not None:
                self._finish_wake()

    def _check_idle(self) -> None:
        with self._lock:
            now = time.monotonic()
            if self._asleep:
                if self._release_deadline is not None and now > self._release_deadline:
                    self._finish_wake()
                return
            minutes = int(self._ctx.config.get('screen_off_minutes', default=5) or 0)
            if minutes and now - self._last_touch > minutes * 60:
                self._sleep()

    # -- state ----------------------------------------------------------------------------------

    def _sleep(self) -> None:
        for device in self._screens:
            device.grab()
        self._backlight.off()
        self._asleep = True
        self._release_deadline = None
        logger.info("Screen off")

    def _finish_wake(self) -> None:
        for device in self._screens:
            try:
                device.ungrab()
            except OSError:
                pass
        self._asleep = False
        self._release_deadline = None
        self._last_touch = time.monotonic()
        logger.info("Screen on")

    def _wake(self) -> None:
        with self._lock:
            if not self._asleep:
                self._last_touch = time.monotonic()
                return
            self._backlight.on()
            self._finish_wake()

    # -- operations -----------------------------------------------------------------------------

    @query(path='/state')
    def get_state(self) -> DisplayState:
        """Whether the box has a screen it can switch off, and whether the screen sleeps now."""
        return DisplayState(available=bool(self._backlight and self._backlight.available), asleep=self._asleep)

    @action()
    def wake(self) -> None:
        """Switch the screen on and start the time until it goes dark anew."""
        if self._thread:
            self._wake()

    @action()
    def sleep(self) -> None:
        """Switch the screen off now."""
        if self._thread:
            with self._lock:
                if not self._asleep:
                    self._sleep()
