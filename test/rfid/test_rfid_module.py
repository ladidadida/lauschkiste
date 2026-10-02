import queue
import threading
import time
from unittest.mock import Mock

import pytest

import lauschkiste.cfghandler
from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.player.module import Player
from lauschkiste.publishing.bus import EventBus
from lauschkiste.rfid.cards import Cards
from lauschkiste.rfid.reader import Rfid


class FakeReader:
    def __init__(self, cards):
        self._cards = cards
        self._stopped = threading.Event()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return self

    def __next__(self):
        if self._stopped.is_set():
            raise StopIteration
        try:
            return self._cards.get(timeout=0.05)
        except queue.Empty:
            return ''

    def stop(self):
        self._stopped.set()


class FakeDriver:
    def __init__(self):
        self.cards = queue.Queue()
        self.created = []

    def create_reader(self, reader_cfg_key):
        self.created.append(reader_cfg_key)
        return FakeReader(self.cards)


MANAGERS = []


@pytest.fixture
def setup(tmp_path):
    main = lauschkiste.cfghandler.get_handler('lauschkiste')
    main.config_dict({})
    (tmp_path / 'cards.yaml').write_text(
        "'0001':\n  action: player.play_folder\n  args:\n    folder: Rock\n"
        "'0002':\n  action: player.next\n"
    )
    (tmp_path / 'rfid.yaml').write_text("rfid:\n  readers:\n    usb:\n      module: fake\n      same_id_delay: 0\n")

    ctrl = Mock()
    driver = FakeDriver()

    class TestPlayer(Player):
        requires = ()

        def start(self, ctx):
            self._ctx = ctx
            self._coordinator = ctrl

        def ready(self):
            pass

        def stop(self):
            return []

    class TestRfid(Rfid):
        def start(self, ctx):
            super().start(ctx)
            self.readers.register('fake', driver)

    cfg = ConfigHandler('test')
    cfg.config_dict({'cards': {'database': str(tmp_path / 'cards.yaml')},
                     'rfid': {'reader_config': str(tmp_path / 'rfid.yaml')}})
    bus = EventBus()
    events = []
    bus.register(lambda topic, payload: events.append((topic, payload)))
    manager = ModuleManager([TestPlayer, Cards, TestRfid], cfg, bus, plugins={}, strict=True)
    manager.load()
    manager.start()
    manager.ready()
    MANAGERS.append(manager)
    yield ctrl, driver, events
    for thread in manager.stop():
        thread.join(2)
    main.config_dict({})


def wait_for(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def test_swiped_card_runs_its_action(setup):
    ctrl, driver, events = setup
    assert driver.created == ['usb']
    driver.cards.put('0001')
    assert wait_for(lambda: ctrl.play_folder.called)
    ctrl.play_folder.assert_called_once_with('Rock', False)
    assert ('rfid.card_detected', {'card_id': '0001', 'registered': True, 'learned': False}) in events


def test_card_without_args_runs(setup):
    ctrl, driver, _ = setup
    driver.cards.put('0002')
    assert wait_for(lambda: ctrl.next.called)


def test_unknown_card_is_published_as_unregistered(setup):
    ctrl, driver, events = setup
    driver.cards.put('9999')
    assert wait_for(lambda: ('rfid.card_detected', {'card_id': '9999', 'registered': False, 'learned': False}) in events)
    ctrl.play_folder.assert_not_called()


def test_learning_reports_the_next_card_without_running_it(setup):
    ctrl, driver, events = setup
    rfid = MANAGERS[-1].handle('rfid')
    rfid.invoke('learn', 30)
    driver.cards.put('0001')
    assert wait_for(lambda: ('rfid.card_detected', {'card_id': '0001', 'registered': True, 'learned': True}) in events)
    time.sleep(0.3)
    ctrl.play_folder.assert_not_called()

    driver.cards.put('0002')
    assert wait_for(lambda: ctrl.next.called)


def test_stop_learning(setup):
    ctrl, driver, _ = setup
    rfid = MANAGERS[-1].handle('rfid')
    rfid.invoke('learn')
    rfid.invoke('stop_learning')
    driver.cards.put('0001')
    assert wait_for(lambda: ctrl.play_folder.called)
