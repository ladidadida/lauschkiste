import queue
import threading

import pytest

from lauschkiste.input_devices import InputDevices

KEYS = {'KEY_PLAYPAUSE': 164, 'KEY_NEXTSONG': 163, 'KEY_VOLUMEUP': 115, 'BTN_TRIGGER': 288}


class FakeDevice:
    def __init__(self, name, path, keys):
        self.name = name
        self.path = path
        self.keys = set(keys)
        self.presses = queue.Queue()
        self.closed = False

    def close(self):
        self.closed = True


class FakeEvdev:
    devices = []

    def key_code(self, key):
        if isinstance(key, int) or str(key).isdigit():
            return int(key)
        return KEYS.get(str(key))

    def key_name(self, code):
        return {v: k for k, v in KEYS.items()}.get(code, str(code))

    def list_devices(self):
        return list(FakeEvdev.devices)

    def key_capabilities(self, device):
        return device.keys

    def key_downs(self, device, stop: threading.Event):
        while not stop.is_set():
            try:
                code = device.presses.get(timeout=0.05)
            except queue.Empty:
                continue
            if code is None:
                raise OSError('disconnected')
            yield code


class FakeInput(InputDevices):
    def __init__(self):
        super().__init__(evdev_access=FakeEvdev)


@pytest.fixture(autouse=True)
def fast_rescan(monkeypatch):
    import lauschkiste.input_devices
    monkeypatch.setattr(lauschkiste.input_devices, 'RESCAN_INTERVAL', 0.05)
    FakeEvdev.devices = []


def test_configured_device_keys_run_actions(start_modules, recorder, recorder_calls, wait_for):
    pad = FakeDevice('DragonRise Inc. Generic USB Joystick', '/dev/input/event5', [288])
    FakeEvdev.devices = [FakeDevice('Keyboard', '/dev/input/event1', [164]), pad]
    config = {'input': {'devices': {'joystick': {
        'device_name': 'DragonRise', 'keys': {'BTN_TRIGGER': {'action': 'recorder.beep', 'args': {'times': 3}}},
    }}}}
    manager, events = start_modules([recorder, FakeInput], config)
    assert wait_for(lambda: manager.handle('input').invoke('list_devices')[0].connected)
    pad.presses.put(288)
    assert wait_for(lambda: recorder_calls == [('beep', 3)])
    assert ('input.key_pressed', {'device': 'joystick', 'key': 'BTN_TRIGGER'}) in events
    assert FakeEvdev.devices[0].closed


def test_legacy_key_mapping_and_reconnect(start_modules, recorder, recorder_calls, wait_for):
    pad = FakeDevice('Pad', '/dev/input/event5', [288])
    FakeEvdev.devices = [pad]
    config = {'input': {'devices': {'pad': {'device_name': 'Pad', 'exact': True,
                                            'keys': {288: {'package': 'recorder', 'plugin': 'beep'}}}}}}
    manager, _ = start_modules([recorder, FakeInput], config)
    handle = manager.handle('input')
    assert wait_for(lambda: handle.invoke('list_devices')[0].connected)
    pad.presses.put(None)
    assert wait_for(lambda: not handle.invoke('list_devices')[0].connected)
    FakeEvdev.devices = [FakeDevice('Pad', '/dev/input/event6', [288])]
    assert wait_for(lambda: handle.invoke('list_devices')[0].path == '/dev/input/event6')
    FakeEvdev.devices[0].presses.put(288)
    assert wait_for(lambda: recorder_calls == [('beep', 1)])


def test_media_keys_attach_to_devices_with_media_keys(start_modules, fake_player, coordinator, wait_for):
    from lauschkiste.volume import Volume
    mouse = FakeDevice('Mouse', '/dev/input/event2', [272])
    headset = FakeDevice('BT Headset', '/dev/input/event9', [164, 115])
    FakeEvdev.devices = [mouse, headset]
    manager, _ = start_modules([fake_player, Volume, FakeInput],
                               {'input': {'media_keys': True}, 'volume': {'mixer': 'player'}})
    assert wait_for(lambda: manager.handle('input').invoke('list_devices')[0].path == headset.path)
    assert mouse.closed
    headset.presses.put(164)
    headset.presses.put(115)
    assert wait_for(lambda: coordinator.toggled == 1 and coordinator.volume == 55)


def test_nothing_configured_opens_nothing(start_modules, recorder):
    FakeEvdev.devices = [FakeDevice('Keyboard', '/dev/input/event1', [164])]
    manager, _ = start_modules([recorder, FakeInput], {})
    assert manager.handle('input').invoke('list_devices') == []
