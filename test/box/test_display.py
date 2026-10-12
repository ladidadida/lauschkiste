import queue
import time

import pytest

from lauschkiste.box.display import Backlight, Display


class FakeBacklight:
    available = True

    def __init__(self):
        self.level = 255

    def off(self):
        self.level = 0

    def on(self):
        self.level = 255


class FakeScreen:
    path = '/dev/input/event0'

    def __init__(self):
        self.grabbed = False
        self.touches = queue.Queue()

    def grab(self):
        self.grabbed = True

    def ungrab(self):
        self.grabbed = False

    def close(self):
        pass


class FakeEvdev:
    screen = None

    def touch_screens(self):
        return [FakeEvdev.screen]

    def read(self, devices, timeout):
        try:
            return [self.screen.touches.get(timeout=0.02)], []
        except queue.Empty:
            return [], []


@pytest.fixture
def screen(monkeypatch):
    import lauschkiste.box.display
    monkeypatch.setattr(lauschkiste.box.display, 'POLL_INTERVAL', 0.02)
    monkeypatch.setattr(lauschkiste.box.display, 'RESCAN_INTERVAL', 0.05)
    FakeEvdev.screen = FakeScreen()
    return FakeEvdev.screen


def display_with(backlight):
    class FakeDisplay(Display):
        def __init__(self):
            super().__init__(backlight, FakeEvdev)

    return FakeDisplay


def start(start_modules, backlight, minutes=10):
    return start_modules([display_with(backlight)], {'display': {'screen_off_minutes': minutes}})[0]


def test_sleep_grabs_the_touch_and_a_touch_wakes_without_reaching_the_app(start_modules, screen, wait_for):
    light = FakeBacklight()
    manager = start(start_modules, light)
    display = manager.handle('display')
    assert wait_for(lambda: screen in display.instance._screens)
    display.invoke('sleep')
    assert light.level == 0 and screen.grabbed
    assert display.invoke('get_state').asleep
    screen.touches.put((True, True))
    assert wait_for(lambda: light.level == 255)
    assert screen.grabbed
    screen.touches.put((True, False))
    assert wait_for(lambda: not screen.grabbed)
    assert not display.invoke('get_state').asleep


def test_goes_dark_after_the_set_time(start_modules, screen, wait_for):
    light = FakeBacklight()
    manager = start(start_modules, light)
    display = manager.handle('display').instance
    display._last_touch = time.monotonic() - 11 * 60
    assert wait_for(lambda: light.level == 0)


def test_zero_minutes_never_switches_off(start_modules, screen):
    light = FakeBacklight()
    manager = start(start_modules, light, minutes=0)
    manager.handle('display').instance._last_touch = time.monotonic() - 99999
    time.sleep(0.2)
    assert light.level == 255


def test_wake_action_ungrabs_at_once(start_modules, screen, wait_for):
    light = FakeBacklight()
    manager = start(start_modules, light)
    display = manager.handle('display')
    assert wait_for(lambda: screen in display.instance._screens)
    display.invoke('sleep')
    display.invoke('wake')
    assert light.level == 255 and not screen.grabbed


def test_no_backlight_means_nothing_happens(start_modules, tmp_path):
    manager = start_modules([display_with(Backlight(tmp_path))], {})[0]
    assert not manager.handle('display').invoke('get_state').available


def test_backlight_keeps_the_brightness_it_found(tmp_path):
    directory = tmp_path / 'panel'
    directory.mkdir()
    (directory / 'brightness').write_text('120')
    (directory / 'max_brightness').write_text('255')
    light = Backlight(tmp_path)
    light.off()
    assert (directory / 'brightness').read_text() == '0'
    light.on()
    assert (directory / 'brightness').read_text() == '120'
