import subprocess
import time
from unittest.mock import Mock

import pytest

import lauschkiste.cfghandler
import lauschkiste_plugin_board_raspberry_pi as board_plugin
from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract import CoreModule, action, extension_point
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.hardware import Hardware
from lauschkiste.player.backend import LevelMeter
from lauschkiste.publishing.bus import EventBus
from lauschkiste_plugin_board_raspberry_pi import bootconfig
from lauschkiste_plugin_devices import phat_beat
from lauschkiste_plugin_devices.apa102 import frame
from lauschkiste_plugin_devices.phat_beat import (BAR, OFF, RAINBOW, RED, VOLUME_COLOR, LedState, level_to_leds,
                                                  shutdown_frames, startup_frames)


class Player(CoreModule):
    name = 'player'
    interface_version = '5.1'
    level_meters = extension_point('level_meters', LevelMeter)
    calls = []

    @action()
    def toggle(self) -> None:
        Player.calls.append('toggle')


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    Player.calls = []
    monkeypatch.setattr(subprocess, 'Popen', Mock())
    lauschkiste.cfghandler.get_handler('lauschkiste').config_dict({})
    yield
    lauschkiste.cfghandler.get_handler('lauschkiste').config_dict({})


@pytest.fixture
def mock_pins(monkeypatch):
    gpiozero = pytest.importorskip('gpiozero')
    from gpiozero.pins.mock import MockFactory
    factory = MockFactory()
    monkeypatch.setattr(phat_beat.PhatBeat, 'pin_factory', factory)
    yield factory
    gpiozero.Device.pin_factory = None


class Writer:
    frames = []

    def __init__(self, chip, data, clock):
        self.lines = (chip, data, clock)

    def write(self, data):
        Writer.frames.append(data)


def start(settings, monkeypatch):
    Writer.frames = []
    monkeypatch.setattr(phat_beat.PhatBeat, 'led_writer', Writer)
    cfg = ConfigHandler('test')
    cfg.config_dict({'plugins': {'board_raspberry_pi': {'debug_mode': True}, 'phat_beat': settings}})
    bus = EventBus()
    manager = ModuleManager([Hardware, Player], cfg, bus, strict=True, plugins={
        'board_raspberry_pi': lambda: board_plugin.BoardRaspberryPi, 'phat_beat': lambda: phat_beat.PhatBeat})
    manager.load()
    manager.start()
    manager.ready()
    assert manager.failed == {}
    return manager, bus


def wait(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not predicate():
        time.sleep(0.01)
    return predicate()


def test_frame_has_start_pixels_in_bgr_and_end():
    data = frame([(1, 2, 3), (4, 5, 6)], brightness=3)
    assert data == b'\x00' * 4 + bytes((0xE3, 3, 2, 1, 0xE3, 6, 5, 4)) + b'\x00' * 4


def test_level_maps_decibels_to_leds():
    assert level_to_leds(0) == 0
    assert level_to_leds(1.0) == BAR
    assert 3.2 < level_to_leds(0.05) < 3.5


def test_volume_overlay_shows_on_both_bars_and_runs_out():
    clock = Clock()
    state = LedState(vu=False, clock=clock)
    state.volume(50)
    pixels = state.pixels()
    assert pixels[:BAR] == [VOLUME_COLOR] * 4 + [OFF] * 4
    assert pixels[BAR:] == [OFF] * 4 + [VOLUME_COLOR] * 4
    clock.now += 3
    assert state.pixels() == [OFF] * 2 * BAR and not state.busy()


def test_level_meter_follows_the_audible_level_and_decays():
    clock = Clock()
    state = LedState(vu=True, clock=clock)
    state.level(1.0, 0.0, delay=0.3)
    assert state.pixels() == [OFF] * 2 * BAR
    clock.now += 0.3
    pixels = state.pixels()
    assert all(color != OFF for color in pixels[:BAR]) and pixels[BAR:] == [OFF] * BAR
    for _ in range(30):
        clock.now += 0.1
        state.pixels()
    assert state.pixels() == [OFF] * 2 * BAR


def test_volume_and_cards_show_over_the_level_meter():
    clock = Clock()
    state = LedState(vu=True, clock=clock)
    state.level(1.0, 1.0, delay=0)
    state.card(registered=False)
    assert state.pixels() == [RED] * 2 * BAR
    clock.now += 0.3
    assert state.pixels() == [OFF] * 2 * BAR
    clock.now += 0.2
    assert state.pixels() == [RED] * 2 * BAR
    clock.now += 0.5
    state.level(1.0, 1.0, delay=0)
    assert all(color != OFF for color in state.pixels())


def test_startup_animation_rises_and_fades_out():
    clock = Clock()
    state = LedState(vu=False, clock=clock)
    state.animate(startup_frames())
    first = state.pixels()
    assert first[0] == RAINBOW[0] and first[1:BAR] == [OFF] * (BAR - 1) and first[-1] == RAINBOW[0]
    clock.now += 0.07 * BAR
    assert state.pixels()[:BAR] == RAINBOW
    clock.now += 2
    assert state.pixels() == [OFF] * 2 * BAR and not state.animating()
    assert shutdown_frames()[-1][0] == [OFF] * 2 * BAR


def test_status_mode_ignores_levels():
    state = LedState(vu=False, clock=Clock())
    state.level(1.0, 1.0, delay=0)
    assert state.pixels() == [OFF] * 2 * BAR


def test_buttons_run_actions_leds_show_volume_and_pins_are_claimed(mock_pins, monkeypatch):
    manager, bus = start({'leds': 'vu'}, monkeypatch)
    time.sleep(0.1)
    mock_pins.pin(6).drive_low()
    assert wait(lambda: Player.calls == ['toggle'])
    assert 'phat_beat' in manager.handle('player').instance.level_meters.names()

    bus.publish('volume.level', {'volume': 100, 'mute': False, 'soft_max_volume': 100})
    lit = frame([VOLUME_COLOR] * 2 * BAR, 3)
    assert wait(lambda: lit in Writer.frames)

    used = {p.id: [u.purpose for u in p.used_by] for p in manager.handle('hardware').invoke('get_state').pins}
    assert used['GPIO6'] == ['button play_pause'] and used['GPIO23'] == ['LED data']
    assert manager.handle('hardware').invoke('get_state').conflicts == []
    manager.stop()
    assert wait(lambda: Writer.frames[-1] == frame([OFF] * 2 * BAR, 3))
    assert frame(shutdown_frames()[0][0], 3) in Writer.frames


def test_power_button_needs_holding(mock_pins, monkeypatch):
    manager, _ = start({'leds': 'off', 'power_hold_time': 0.5}, monkeypatch)
    shutdown = Mock()
    monkeypatch.setattr(board_plugin.RaspberryPiBoard, 'shutdown', lambda self: shutdown())
    mock_pins.pin(12).drive_low()
    time.sleep(0.2)
    assert not shutdown.called
    assert wait(lambda: shutdown.called)
    assert Writer.frames == []
    manager.stop()


def test_boot_configuration_switches_its_dac_on():
    want = bootconfig.wanted({'plugins': {'board_raspberry_pi': {}, 'phat_beat': {}}})
    assert want.sound_card == 'hifiberry-dac' and not want.onboard_audio
    chosen = bootconfig.wanted({'plugins': {'board_raspberry_pi': {'sound_card': 'max98357a'}, 'phat_beat': {}}})
    assert chosen.sound_card == 'max98357a'
