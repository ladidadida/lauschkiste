"""Pimoroni pHAT BEAT (e.g. in the Pirate Radio): six buttons, two bars of eight LEDs, an I²S DAC.

::

    plugins:
      phat_beat:
        leds: vu                     # vu, status or off
        volume_up: {action: volume.change_volume, args: {step: 5}}

The DAC is a sound card of the board (Raspberry Pi: hifiberry-dac); the board plugin's boot
configuration switches it on when this plugin is enabled.
"""

import logging
import math
import threading
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

from lauschkiste.contract import ActionEntry, Plugin
from lauschkiste.hardware import Claim

from lauschkiste_plugin_devices.apa102 import Color, LgpioWriter, frame
from lauschkiste_plugin_devices.gpio import Pins

logger = logging.getLogger('lauschkiste.phat_beat')

BUTTONS = {'play_pause': 'GPIO6', 'next': 'GPIO5', 'previous': 'GPIO13',
           'volume_up': 'GPIO16', 'volume_down': 'GPIO26', 'power': 'GPIO12'}
REPEATING = ('volume_up', 'volume_down')
LED_DATA, LED_CLOCK = 'GPIO23', 'GPIO24'
BAR = 8
OFF: Color = (0, 0, 0)
VU_COLORS: List[Color] = [(0, 255, 0)] * 5 + [(255, 160, 0)] * 2 + [(255, 0, 0)]
VOLUME_COLOR: Color = (0, 80, 255)
OVERLAY_SECONDS = {'volume': 2.0, 'card': 0.6, 'unknown_card': 1.2}
#: Level in dB shown by an empty and a full bar
VU_RANGE_DB = (-45.0, 0.0)


def _action(action: str, **args) -> ActionEntry:
    return ActionEntry(action=action, args=args)


class PhatBeatSettings(BaseModel):
    play_pause: Optional[ActionEntry] = Field(_action('player.toggle'), title='Play/pause button')
    next: Optional[ActionEntry] = Field(_action('player.next'), title='Next button')
    previous: Optional[ActionEntry] = Field(_action('player.prev'), title='Previous button')
    volume_up: Optional[ActionEntry] = Field(_action('volume.change_volume', step=5), title='Volume up button',
                                             description='Repeats while held')
    volume_down: Optional[ActionEntry] = Field(_action('volume.change_volume', step=-5), title='Volume down button',
                                               description='Repeats while held')
    power: Optional[ActionEntry] = Field(_action('hardware.shutdown'), title='On/off button (held)')
    power_hold_time: float = Field(2.0, ge=0.5, le=10, title='Hold the on/off button for (seconds)')
    leds: Literal['vu', 'status', 'off'] = Field('status', title='LEDs',
                                                 description='vu: level meter while playing; status: volume and cards')
    brightness: int = Field(3, ge=1, le=31, title='LED brightness')


def _bar(count: float, colors: List[Color]) -> List[Color]:
    return [colors[i] if i < round(count) else OFF for i in range(BAR)]


def _pixels(left: List[Color], right: List[Color]) -> List[Color]:
    """Channel 0 runs from pixel 0 upwards, channel 1 from pixel 15 downwards."""
    return left + list(reversed(right))


def level_to_leds(rms: float) -> float:
    if rms <= 0:
        return 0.0
    low, high = VU_RANGE_DB
    return max(0.0, min(float(BAR), (20 * math.log10(rms) - low) / (high - low) * BAR))


class LedState:
    """What the LEDs show: a short overlay (volume, card) over the level meter or darkness."""

    DECAY = 0.75

    def __init__(self, vu: bool, clock: Callable[[], float] = time.monotonic):
        self._vu = vu
        self._clock = clock
        self._lock = threading.Lock()
        self._overlay: Optional[Tuple[List[Color], float]] = None
        self._levels: Deque[Tuple[float, float, float]] = deque(maxlen=50)
        self._left = self._right = 0.0

    def volume(self, volume: int) -> None:
        bar = _bar(BAR * max(0, min(100, volume)) / 100, [VOLUME_COLOR] * BAR)
        self._show(_pixels(bar, bar), OVERLAY_SECONDS['volume'])

    def card(self, registered: bool) -> None:
        color = (0, 255, 0) if registered else (255, 0, 0)
        self._show([color] * 2 * BAR, OVERLAY_SECONDS['card' if registered else 'unknown_card'])

    def level(self, left: float, right: float, delay: float) -> None:
        if self._vu:
            with self._lock:
                self._levels.append((self._clock() + delay, level_to_leds(left), level_to_leds(right)))

    def _show(self, pixels: List[Color], seconds: float) -> None:
        with self._lock:
            self._overlay = (pixels, self._clock() + seconds)

    def busy(self) -> bool:
        """True while the picture changes by itself (an overlay runs out, the meter moves)."""
        with self._lock:
            return self._overlay is not None or bool(self._levels) or self._left > 0.05 or self._right > 0.05

    def pixels(self) -> List[Color]:
        now = self._clock()
        with self._lock:
            target_left = target_right = 0.0
            while self._levels and self._levels[0][0] <= now:
                _, target_left, target_right = self._levels.popleft()
            self._left = max(target_left, self._left * self.DECAY)
            self._right = max(target_right, self._right * self.DECAY)
            if self._overlay is not None:
                if now < self._overlay[1]:
                    return list(self._overlay[0])
                self._overlay = None
            if not self._vu:
                return [OFF] * 2 * BAR
            return _pixels(_bar(self._left, VU_COLORS), _bar(self._right, VU_COLORS))


class Leds:
    """Draws the LED state about ten times a second while it changes; writes only changed frames."""

    def __init__(self, state: LedState, write: Callable[[bytes], None], brightness: int):
        self._state = state
        self._write = write
        self._brightness = brightness
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name='phat_beat.leds', daemon=True)

    def start(self) -> None:
        self._thread.start()

    def wake(self) -> None:
        self._wake.set()

    def stop(self) -> threading.Thread:
        self._stop.set()
        self._wake.set()
        return self._thread

    def _run(self) -> None:
        last: Optional[List[Color]] = None
        while not self._stop.is_set():
            pixels = self._state.pixels()
            if pixels != last:
                try:
                    self._write(frame(pixels, self._brightness))
                except Exception as error:
                    logger.error(f"LEDs: {error.__class__.__name__}: {error}")
                    return
                last = pixels
            self._wake.wait(0.1 if self._state.busy() else 5.0)
            self._wake.clear()
        try:
            self._write(frame([OFF] * 2 * BAR, self._brightness))
        except Exception:
            pass


class Buttons:
    def __init__(self, config: Dict[str, Any], bind: Callable[[Dict[str, Any]], Optional[Callable[[], None]]], pins: Pins):
        import gpiozero
        self._devices: List[Any] = []
        for name, pin in BUTTONS.items():
            entry = config.get(name)
            run = bind(entry) if entry else None
            if run is None:
                continue
            try:
                self._devices.append(self._button(gpiozero, name, pin, run, config, pins))
            except Exception as error:
                logger.error(f"Button '{name}' on {pin}: {error.__class__.__name__}: {error}")

    @staticmethod
    def _button(gpiozero, name: str, pin: str, run, config: Dict[str, Any], pins: Pins):
        line = pins.line(pin)
        if name == 'power':
            button = gpiozero.Button(line, pull_up=True, bounce_time=0.05,
                                     hold_time=config['power_hold_time'], **pins.kwargs())
            button.when_held = run
        elif name in REPEATING:
            button = gpiozero.Button(line, pull_up=True, bounce_time=0.05, hold_time=0.5, hold_repeat=True,
                                     **pins.kwargs())
            button.when_pressed = run
            button.when_held = run
        else:
            button = gpiozero.Button(line, pull_up=True, bounce_time=0.05, **pins.kwargs())
            button.when_pressed = run
        return button

    def close(self) -> None:
        for device in self._devices:
            try:
                device.close()
            except Exception as error:
                logger.debug(f"Closing a button failed: {error}")
        self._devices = []


def settings_of(ctx) -> Dict[str, Any]:
    """The settings with their defaults (the config holds only what was changed)."""
    try:
        return PhatBeatSettings.model_validate(ctx.config.as_dict()).model_dump()
    except ValueError as error:
        logger.error(f"Invalid settings, using the defaults: {error}")
        return PhatBeatSettings().model_dump()


class PhatBeatClaims:
    def __init__(self, ctx):
        self._ctx = ctx

    def claims(self) -> List[Claim]:
        config = settings_of(self._ctx)
        result = [Claim(resource=pin, owner='phat_beat', purpose=f'button {name}') for name, pin in BUTTONS.items()]
        if config['leds'] != 'off':
            result += [Claim(resource=LED_DATA, owner='phat_beat', purpose='LED data'),
                       Claim(resource=LED_CLOCK, owner='phat_beat', purpose='LED clock')]
        result.append(Claim(resource='i2s', owner='phat_beat', purpose='DAC', shared=True))
        return result


class PhatBeat(Plugin):
    """Pimoroni pHAT BEAT: buttons, LED bars (volume, cards, level meter) and its DAC."""

    name = 'phat_beat'
    interface_version = '1.0'
    needs = ('gpio', 'i2s')
    requires = {'hardware': '>=1.0,<2', 'player': '>=5.1,<6'}
    extras = ('gpio',)
    settings = PhatBeatSettings
    pin_factory = None
    led_writer: Optional[Callable[[int, int, int], Any]] = None

    def __init__(self):
        self._ctx: Any = None
        self._buttons: Optional[Buttons] = None
        self._state: Optional[LedState] = None
        self._leds: Optional[Leds] = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        ctx.modules.hardware.claims.register('phat_beat', PhatBeatClaims(ctx))
        mode = settings_of(ctx)['leds']
        if mode != 'off':
            self._state = LedState(vu=mode == 'vu')
            if mode == 'vu':
                ctx.modules.player.level_meters.register('phat_beat', self)
            ctx.subscribe('volume.level', self._on_volume)
            ctx.subscribe('rfid.card_detected', self._on_card)

    def ready(self) -> None:
        config = settings_of(self._ctx)
        pins = Pins(self._ctx.modules.hardware, self.pin_factory)
        self._buttons = Buttons(config, self._bind, pins)
        if self._state is not None:
            try:
                data, clock = pins.line(LED_DATA), pins.line(LED_CLOCK)
                writer = (self.led_writer or LgpioWriter)(pins.chip, data, clock)
            except Exception as error:
                logger.error(f"LEDs not available: {error.__class__.__name__}: {error}")
                return
            self._leds = Leds(self._state, writer.write, config['brightness'])
            self._leds.start()

    def stop(self):
        threads = []
        if self._buttons is not None:
            self._buttons.close()
        if self._leds is not None:
            threads.append(self._leds.stop())
        return threads

    def settings_changed(self, changed) -> bool:
        return False

    def _bind(self, entry):
        return self._ctx.actions.bind(entry, 'phat_beat', logger)

    def level(self, left: float, right: float, delay: float) -> None:
        if self._state is not None:
            idle = not self._state.busy()
            self._state.level(left, right, delay)
            if idle and self._leds is not None:
                self._leds.wake()

    def _on_volume(self, _topic: str, payload: Optional[Dict[str, Any]]) -> None:
        if payload and self._state is not None and self._leds is not None:
            self._state.volume(int(payload.get('volume', 0)))
            self._leds.wake()

    def _on_card(self, _topic: str, payload: Optional[Dict[str, Any]]) -> None:
        if payload and self._state is not None and self._leds is not None:
            self._state.card(bool(payload.get('registered')))
            self._leds.wake()
