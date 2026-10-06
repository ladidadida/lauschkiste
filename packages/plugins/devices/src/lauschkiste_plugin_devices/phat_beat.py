"""Pimoroni pHAT BEAT (e.g. in the Pirate Radio): six buttons, two bars of eight LEDs, an I²S DAC.

::

    plugins:
      phat_beat:
        leds: vu                     # vu, status or off
        volume_up: {action: volume.change_volume, args: {step: 5}}

The DAC is a sound card of the board (Raspberry Pi: hifiberry-dac); the board plugin's boot
configuration switches it on when this plugin is enabled.
"""

import colorsys
import logging
import math
import threading
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

from lauschkiste.contract import ActionEntry, Plugin
from lauschkiste.hardware import Claim

from lauschkiste_plugin_devices.apa102 import Color, frame, writer
from lauschkiste_plugin_devices.gpio import Pins

logger = logging.getLogger('lauschkiste.phat_beat')

BUTTONS = {'play_pause': 'GPIO6', 'next': 'GPIO5', 'previous': 'GPIO13',
           'volume_up': 'GPIO16', 'volume_down': 'GPIO26', 'power': 'GPIO12'}
REPEATING = ('volume_up', 'volume_down')
LED_DATA, LED_CLOCK = 'GPIO23', 'GPIO24'
BAR = 8
OFF: Color = (0, 0, 0)
VOLUME_COLOR: Color = (0, 80, 255)
GREEN: Color = (0, 255, 0)
RED: Color = (255, 0, 0)
RAINBOW: List[Color] = [tuple(round(255 * c) for c in colorsys.hsv_to_rgb(0.75 * i / (BAR - 1), 1, 1))
                        for i in range(BAR)]


def gradient(*stops: Color) -> List[Color]:
    """Eight colors from the first stop (bottom) to the last (top)."""
    colors = []
    for i in range(BAR):
        position = i / (BAR - 1) * (len(stops) - 1)
        index = min(int(position), len(stops) - 2)
        f = position - index
        low, high = stops[index], stops[index + 1]
        colors.append(tuple(round(a + (b - a) * f) for a, b in zip(low, high)))
    return colors


#: Colors of the bars from bottom to top
PALETTES: Dict[str, List[Color]] = {
    'classic': [(0, 255, 0)] * 5 + [(255, 160, 0)] * 2 + [(255, 0, 0)],
    'rainbow': RAINBOW,
    'ocean': gradient((0, 255, 160), (0, 120, 255), (120, 0, 255)),
    'sunset': gradient((255, 200, 0), (255, 70, 0), (255, 0, 120)),
    'unicorn': gradient((255, 90, 200), (170, 70, 255), (60, 200, 255)),
    'forest': gradient((200, 255, 0), (0, 210, 50), (0, 140, 130)),
    'fire': gradient((255, 20, 0), (255, 120, 0), (255, 230, 90)),
}
Palette = Literal['classic', 'rainbow', 'ocean', 'sunset', 'unicorn', 'forest', 'fire']
VOLUME_SECONDS = 2.0
#: A picture and how long it stays
Frames = List[Tuple[List[Color], float]]
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
    leds: Literal['vu', 'status', 'off'] = Field('status', title='LEDs', description=(
        'vu: level meter while playing, volume and cards shown over it; status: only volume and cards'))
    colors: Palette = Field('classic', title='Colors', description=(
        'Colors of the level meter and the animations, bottom to top'))
    animations: bool = Field(True, title='Start and shutdown animation')
    brightness: int = Field(3, ge=1, le=31, title='LED brightness')


def _bar(count: float, colors: List[Color]) -> List[Color]:
    return [colors[i] if i < round(count) else OFF for i in range(BAR)]


def _pixels(left: List[Color], right: List[Color]) -> List[Color]:
    """Channel 0 runs from pixel 0 upwards, channel 1 from pixel 15 downwards."""
    return left + list(reversed(right))


def _scaled(colors: List[Color], factor: float) -> List[Color]:
    return [(round(r * factor), round(g * factor), round(b * factor)) for r, g, b in colors]


def startup_frames(colors: List[Color] = RAINBOW) -> Frames:
    """The bars fill up in ``colors``, stay a moment and fade out."""
    frames: Frames = [(_pixels(_bar(n, colors), _bar(n, colors)), 0.07) for n in range(1, BAR + 1)]
    frames.append((_pixels(colors, colors), 0.4))
    frames += [(_pixels(_scaled(colors, f), _scaled(colors, f)), 0.08) for f in (0.6, 0.35, 0.15, 0.05)]
    return frames


def shutdown_frames(colors: List[Color] = RAINBOW) -> Frames:
    """The bars sink down, top first."""
    return [(_pixels(_bar(n, colors), _bar(n, colors)), 0.06) for n in range(BAR, -1, -1)]


def card_frames(registered: bool) -> Frames:
    if registered:
        return [([GREEN] * 2 * BAR, 0.6)]
    return [([RED] * 2 * BAR, 0.25), ([OFF] * 2 * BAR, 0.15)] * 2


def level_to_leds(rms: float) -> float:
    if rms <= 0:
        return 0.0
    low, high = VU_RANGE_DB
    return max(0.0, min(float(BAR), (20 * math.log10(rms) - low) / (high - low) * BAR))


class LedState:
    """What the LEDs show: short animations (start, volume, cards) over the level meter or darkness."""

    DECAY = 0.75

    def __init__(self, vu: bool, colors: Optional[List[Color]] = None, clock: Callable[[], float] = time.monotonic):
        self._vu = vu
        self.colors = colors or PALETTES['classic']
        self._clock = clock
        self._lock = threading.Lock()
        self._overlay: Optional[Tuple[float, Frames]] = None
        self._levels: Deque[Tuple[float, float, float]] = deque(maxlen=50)
        self._left = self._right = 0.0

    def volume(self, volume: int) -> None:
        bar = _bar(BAR * max(0, min(100, volume)) / 100, [VOLUME_COLOR] * BAR)
        self.animate([(_pixels(bar, bar), VOLUME_SECONDS)])

    def card(self, registered: bool) -> None:
        self.animate(card_frames(registered))

    def level(self, left: float, right: float, delay: float) -> None:
        if self._vu:
            with self._lock:
                self._levels.append((self._clock() + delay, level_to_leds(left), level_to_leds(right)))

    def animate(self, frames: Frames) -> None:
        """Show ``frames`` now, replacing what is shown over the meter."""
        with self._lock:
            self._overlay = (self._clock(), frames)

    def animating(self) -> bool:
        with self._lock:
            return self._overlay is not None

    def busy(self) -> bool:
        """True while the picture changes by itself (an animation runs, the meter moves)."""
        with self._lock:
            return self._overlay is not None or bool(self._levels) or self._left > 0.05 or self._right > 0.05

    def _overlay_pixels(self, now: float) -> Optional[List[Color]]:
        if self._overlay is None:
            return None
        start, frames = self._overlay
        for pixels, seconds in frames:
            start += seconds
            if now < start:
                return list(pixels)
        self._overlay = None
        return None

    def pixels(self) -> List[Color]:
        now = self._clock()
        with self._lock:
            target_left = target_right = 0.0
            while self._levels and self._levels[0][0] <= now:
                _, target_left, target_right = self._levels.popleft()
            self._left = max(target_left, self._left * self.DECAY)
            self._right = max(target_right, self._right * self.DECAY)
            overlay = self._overlay_pixels(now)
            if overlay is not None:
                return overlay
            if not self._vu:
                return [OFF] * 2 * BAR
            return _pixels(_bar(self._left, self.colors), _bar(self._right, self.colors))


class Leds:
    """Draws the LED state about ten times a second while it changes; writes only changed frames."""

    def __init__(self, state: LedState, write: Callable[[bytes], None], brightness: int, animations: bool = True):
        self._state = state
        self._animations = animations
        self._write = write
        self._brightness = brightness
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name='phat_beat.leds', daemon=True)

    def start(self) -> None:
        if self._animations:
            self._state.animate(startup_frames(self._state.colors))
        self._thread.start()

    def wake(self) -> None:
        self._wake.set()

    def stop(self) -> threading.Thread:
        if self._animations:
            self._state.animate(shutdown_frames(self._state.colors))
        self._stop.set()
        self._wake.set()
        return self._thread

    def _run(self) -> None:
        last: Optional[List[Color]] = None
        while not self._stop.is_set() or self._state.animating():
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


class LgpioButtons:
    """Reads the levels of all button lines with one call (pull-ups on, pressed = low)."""

    def __init__(self, chip: int, lines: List[int]):
        import lgpio
        self._lgpio = lgpio
        self._handle = lgpio.gpiochip_open(chip)
        self._leader = lines[0]
        self._count = len(lines)
        try:
            lgpio.group_claim_input(self._handle, lines, lgpio.SET_PULL_UP)
        except Exception:
            lgpio.gpiochip_close(self._handle)
            raise

    def pressed(self) -> List[bool]:
        _, levels = self._lgpio.group_read(self._handle, self._leader)
        return [not (levels >> i) & 1 for i in range(self._count)]

    def close(self) -> None:
        self._lgpio.gpiochip_close(self._handle)


class Button:
    def __init__(self, press: Optional[Callable[[], None]] = None, hold: Optional[Callable[[], None]] = None,
                 hold_time: float = 1.0, repeat: Optional[float] = None):
        self.press, self.hold, self.hold_time, self.repeat = press, hold, hold_time, repeat
        self.down: Optional[float] = None
        self.fired: Optional[float] = None


class Buttons:
    """Polls the buttons 20 times a second. gpiozero's edge detection (through lgpio) keeps 13 % of a
    Pi Zero's CPU busy; this needs a fraction of one percent."""

    INTERVAL = 0.05

    def __init__(self, read: Callable[[], List[bool]], buttons: List[Button], clock: Callable[[], float] = time.monotonic):
        self._read = read
        self._buttons = buttons
        self._clock = clock
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name='phat_beat.buttons', daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> threading.Thread:
        self._stop.set()
        return self._thread

    def _run(self) -> None:
        while not self._stop.wait(self.INTERVAL):
            try:
                self.poll()
            except Exception as error:
                logger.error(f"Buttons: {error.__class__.__name__}: {error}")
                return

    def poll(self) -> None:
        now = self._clock()
        for button, pressed in zip(self._buttons, self._read()):
            if not pressed:
                button.down = button.fired = None
                continue
            if button.down is None:
                button.down = now
                if button.press is not None:
                    button.press()
            elif button.hold is not None and now - button.down >= button.hold_time:
                if button.fired is None or (button.repeat is not None and now - button.fired >= button.repeat):
                    button.fired = now
                    button.hold()


def buttons_from(config: Dict[str, Any], bind: Callable[[Dict[str, Any]], Optional[Callable[[], None]]]) -> Dict[str, Button]:
    result = {}
    for name in BUTTONS:
        run = bind(config[name]) if config.get(name) else None
        if run is None:
            continue
        if name == 'power':
            result[name] = Button(hold=run, hold_time=config['power_hold_time'])
        elif name in REPEATING:
            result[name] = Button(press=run, hold=run, hold_time=0.5, repeat=0.25)
        else:
            result[name] = Button(press=run)
    return result


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
    button_reader: Optional[Callable[[int, List[int]], Any]] = None
    led_writer: Optional[Callable[[int, int, int], Any]] = None

    def __init__(self):
        self._ctx: Any = None
        self._buttons: Optional[Buttons] = None
        self._button_lines: Any = None
        self._state: Optional[LedState] = None
        self._leds: Optional[Leds] = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        ctx.modules.hardware.claims.register('phat_beat', PhatBeatClaims(ctx))
        config = settings_of(ctx)
        mode = config['leds']
        if mode != 'off':
            self._state = LedState(vu=mode == 'vu', colors=PALETTES[config['colors']])
            if mode == 'vu':
                ctx.modules.player.level_meters.register('phat_beat', self)
            ctx.subscribe('volume.level', self._on_volume)
            ctx.subscribe('rfid.card_detected', self._on_card)

    def ready(self) -> None:
        config = settings_of(self._ctx)
        pins = Pins(self._ctx.modules.hardware)
        buttons = buttons_from(config, self._bind)
        if buttons:
            try:
                lines = [pins.line(BUTTONS[name]) for name in buttons]
                self._button_lines = (self.button_reader or LgpioButtons)(pins.chip, lines)
                self._buttons = Buttons(self._button_lines.pressed, list(buttons.values()))
                self._buttons.start()
            except Exception as error:
                logger.error(f"Buttons not available: {error.__class__.__name__}: {error}")
        if self._state is not None:
            try:
                data, clock = pins.line(LED_DATA), pins.line(LED_CLOCK)
                leds = (self.led_writer or writer)(pins.chip, data, clock)
            except Exception as error:
                logger.error(f"LEDs not available: {error.__class__.__name__}: {error}")
                return
            logger.info(f"LEDs through {type(leds).__name__}")
            self._leds = Leds(self._state, leds.write, config['brightness'], config['animations'])
            self._leds.start()

    def stop(self):
        threads = []
        if self._buttons is not None:
            threads.append(self._buttons.stop())
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
