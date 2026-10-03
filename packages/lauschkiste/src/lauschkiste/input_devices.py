"""The input core module: keys of evdev input devices (USB buttons, keyboards, headset buttons) run actions.

Configured under ``input:``::

    input:
      media_keys: false          # play/pause/next/volume keys of any device (e.g. a Bluetooth headset)
      devices:
        joystick:
          device_name: DragonRise Inc.   Generic   USB
          exact: false           # substring match of the device name
          keys:
            BTN_TRIGGER: {action: player.toggle}
            297: {action: player.prev}
"""

import logging
import select
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from lauschkiste.contract import CoreModule, event, query

logger = logging.getLogger('lauschkiste.input')

RESCAN_INTERVAL = 3.0

MEDIA_KEYS: Dict[str, Dict[str, Any]] = {
    'KEY_PLAYPAUSE': {'action': 'player.toggle'},
    'KEY_PLAYCD': {'action': 'player.play'},
    'KEY_PAUSECD': {'action': 'player.pause'},
    'KEY_STOPCD': {'action': 'player.stop'},
    'KEY_NEXTSONG': {'action': 'player.next'},
    'KEY_PREVIOUSSONG': {'action': 'player.prev'},
    'KEY_VOLUMEUP': {'action': 'volume.change_volume', 'args': {'step': 5}},
    'KEY_VOLUMEDOWN': {'action': 'volume.change_volume', 'args': {'step': -5}},
    'KEY_MUTE': {'action': 'volume.mute'},
}
MEDIA_KEYS_DEVICE = 'media_keys'


class KeyPressed(BaseModel):
    device: str
    key: str


class DeviceState(BaseModel):
    name: str
    device_name: str
    connected: bool
    path: Optional[str] = None


@dataclass
class _Binding:
    action: str
    args: Dict[str, Any]


@dataclass
class _Watch:
    name: str
    device_name: Optional[str]
    exact: bool
    bindings: Dict[int, _Binding]
    threads: Dict[str, threading.Thread] = field(default_factory=dict)


class Evdev:
    """Access to the evdev library; replaced in tests."""

    def __init__(self):
        import evdev
        self._evdev = evdev

    def key_code(self, key) -> Optional[int]:
        if isinstance(key, int) or str(key).isdigit():
            return int(key)
        code = self._evdev.ecodes.ecodes.get(str(key))
        return code if isinstance(code, int) else None

    def key_name(self, code: int) -> str:
        name = self._evdev.ecodes.KEY.get(code) or self._evdev.ecodes.BTN.get(code)
        if isinstance(name, list):
            name = name[0]
        return name or str(code)

    def list_devices(self) -> List[Any]:
        devices = []
        for path in self._evdev.list_devices():
            try:
                devices.append(self._evdev.InputDevice(path))
            except OSError:
                continue
        return devices

    def key_capabilities(self, device) -> set:
        return set(device.capabilities().get(self._evdev.ecodes.EV_KEY, []))

    def key_downs(self, device, stop: threading.Event):
        """Yield key codes pressed on ``device`` until ``stop`` is set; raises OSError on disconnect."""
        while not stop.is_set():
            readable, _, _ = select.select([device], [], [], 0.2)
            if not readable:
                continue
            for input_event in device.read():
                if input_event.type == self._evdev.ecodes.EV_KEY and input_event.value == 1:
                    yield input_event.code


class InputSettings(BaseModel):
    media_keys: bool = Field(False, title='Media keys of all devices',
                             description='Play/pause, next, previous and volume keys, e.g. of a Bluetooth headset')


class InputDevices(CoreModule):
    """Keys of input devices run actions."""

    name = 'input'
    interface_version = '1.0'
    concurrency = 'threadsafe'
    settings = InputSettings

    key_pressed = event('key_pressed', KeyPressed)

    def __init__(self, evdev_access: Optional[Callable[[], Any]] = None):
        self._ctx = None
        self._evdev_factory = evdev_access or Evdev
        self._evdev = None
        self._watches: List[_Watch] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._scanner: Optional[threading.Thread] = None
        self._dispatch = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._dispatch = ctx.executor('dispatch')

    def ready(self) -> None:
        config = self._ctx.config.as_dict()
        devices = config.get('devices') or {}
        if not devices and not config.get('media_keys', False):
            return
        try:
            self._evdev = self._evdev_factory()
        except ImportError as error:
            logger.error(f"Input devices need evdev: {error}")
            return
        for name, device in devices.items():
            bindings = self._bindings(name, device.get('keys') or {})
            if bindings:
                self._watches.append(_Watch(name, str(device.get('device_name', '')), bool(device.get('exact', False)),
                                            bindings))
        if config.get('media_keys', False):
            self._watches.append(_Watch(MEDIA_KEYS_DEVICE, None, False, self._bindings(MEDIA_KEYS_DEVICE, MEDIA_KEYS)))
        if self._watches:
            self._scanner = threading.Thread(target=self._scan_loop, name='input.scan', daemon=True)
            self._scanner.start()

    def stop(self) -> List[threading.Thread]:
        self._stop.set()
        with self._lock:
            threads = [t for w in self._watches for t in w.threads.values()]
        return [*threads, *([self._scanner] if self._scanner else [])]

    def _bindings(self, device: str, keys: Dict[Any, Any]) -> Dict[int, _Binding]:
        catalog = self._ctx.actions
        bindings = {}
        for key, entry in keys.items():
            code = self._evdev_code(key)
            if code is None:
                logger.error(f"Input '{device}': unknown key '{key}'")
                continue
            if not isinstance(entry, dict) or not isinstance(entry.get('action'), str):
                logger.error(f"Input '{device}', key '{key}': expected 'action: <module>.<action>', got {entry!r}")
                continue
            args = entry.get('args') or {}
            try:
                catalog.validate(entry['action'], args)
            except Exception as error:
                if device != MEDIA_KEYS_DEVICE:
                    logger.error(f"Input '{device}', key '{key}': {error}")
                continue
            bindings[code] = _Binding(entry['action'], args)
        return bindings

    def _evdev_code(self, key) -> Optional[int]:
        if self._evdev is None:
            self._evdev = self._evdev_factory()
        return self._evdev.key_code(key)

    # -- device handling ------------------------------------------------------------------------

    def _matches(self, watch: _Watch, device) -> bool:
        if watch.device_name is None:
            return bool(set(watch.bindings) & self._evdev.key_capabilities(device))
        if watch.exact:
            return device.name == watch.device_name
        return watch.device_name in device.name

    def _scan_loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._scan()
            except Exception:
                logger.exception("Scanning input devices failed")
            self._stop.wait(RESCAN_INTERVAL)

    def _scan(self) -> None:
        for device in self._evdev.list_devices():
            claimed = False
            with self._lock:
                for watch in self._watches:
                    if device.path in watch.threads or not self._matches(watch, device):
                        continue
                    if watch.device_name is not None and watch.threads:
                        continue
                    thread = threading.Thread(target=self._listen, args=(watch, device),
                                              name=f'input.{watch.name}', daemon=True)
                    watch.threads[device.path] = thread
                    thread.start()
                    claimed = True
                    break
            if not claimed:
                device.close()

    def _listen(self, watch: _Watch, device) -> None:
        logger.info(f"Input '{watch.name}': listening to '{device.name}' ({device.path})")
        try:
            for code in self._evdev.key_downs(device, self._stop):
                binding = watch.bindings.get(code)
                if binding is None:
                    continue
                self._ctx.publish(self.key_pressed, KeyPressed(device=watch.name, key=self._evdev.key_name(code)))
                self._dispatch.submit(self._ctx.actions.call_ignore_errors, binding.action, binding.args)
        except OSError as error:
            logger.info(f"Input '{watch.name}': '{device.path}' disconnected ({error})")
        finally:
            device.close()
            with self._lock:
                watch.threads.pop(device.path, None)

    # -- operations -----------------------------------------------------------------------------

    @query(path='/devices')
    def list_devices(self) -> List[DeviceState]:
        """Configured input devices and whether they are connected."""
        with self._lock:
            return [DeviceState(name=w.name, device_name=w.device_name or '(any device with media keys)',
                                connected=bool(w.threads), path=next(iter(w.threads), None)) for w in self._watches]
