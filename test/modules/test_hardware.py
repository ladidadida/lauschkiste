import pytest

from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract import OperationError, Plugin
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.hardware import Claim, Hardware
from lauschkiste.publishing.bus import EventBus


class FakeBoard:
    def __init__(self):
        self.calls = []

    def describe(self):
        return {'name': 'fake', 'model': 'Fake Board 1', 'pins': [
            {'id': 'GPIO2', 'label': 'GPIO2 (pin 3)', 'position': 3, 'functions': ['gpio', 'i2c1.sda']},
            {'id': 'GPIO3', 'label': 'GPIO3 (pin 5)', 'position': 5, 'functions': ['gpio', 'i2c1.scl']},
            {'id': 'GPIO5', 'label': 'GPIO5 (pin 29)', 'position': 29, 'functions': ['gpio']},
            {'id': '5V', 'label': '5V (pin 2)', 'position': 2, 'functions': ['power']},
        ], 'interfaces': [{'id': 'i2c1', 'label': 'I²C 1', 'pins': ['GPIO2', 'GPIO3']}]}

    def pin_id(self, value):
        text = str(value).upper()
        text = text if text.startswith('GPIO') else f'GPIO{text}'
        return text if text in ('GPIO2', 'GPIO3', 'GPIO5') else None

    def gpio_line(self, pin):
        return 0, int(pin[4:])

    def shutdown(self):
        self.calls.append('shutdown')

    def reboot(self):
        self.calls.append('reboot')

    def boot_pending(self):
        return ['i2c']


class Claims:
    def __init__(self, claims):
        self.list = claims

    def claims(self):
        return self.list


def manager_with(board=None, claims=()):
    class Devices(Plugin):
        name = 'devices'
        requires = ('hardware',)

        def start(self, ctx):
            hardware = ctx.modules.hardware
            if board is not None:
                hardware.boards.register('fake', board)
            for index, entry in enumerate(claims):
                hardware.claims.register(f'c{index}', Claims(entry))

    manager = ModuleManager([Hardware], ConfigHandler('test'), EventBus(), plugins={'devices': lambda: Devices},
                            strict=True)
    manager._cfg.config_dict({'plugins': {'devices': {}}})
    manager.load()
    manager.start()
    manager.ready()
    return manager.handle('hardware')


def test_pins_users_and_shared_buses():
    hardware = manager_with(FakeBoard(), [
        [Claim(resource='i2c1', owner='battery', purpose='MAX17048')],
        [Claim(resource='i2c1', owner='clock', purpose='RTC')],
        [Claim(resource='5', owner='gpio_controls', purpose='button next')],
    ])
    state = hardware.invoke('get_state')
    pins = {pin.id: pin for pin in state.pins}
    assert (state.board, state.model, state.boot_pending) == ('fake', 'Fake Board 1', ['i2c'])
    assert [u.owner for u in pins['GPIO2'].used_by] == ['battery', 'clock']
    assert state.conflicts == []
    assert pins['GPIO5'].used_by[0].purpose == 'button next'


def test_conflicts_and_unknown_pins():
    hardware = manager_with(FakeBoard(), [
        [Claim(resource='i2c1', owner='battery')],
        [Claim(resource='GPIO2', owner='gpio_controls', purpose='button'),
         Claim(resource='GPIO99', owner='gpio_controls', purpose='led')],
        [Claim(resource='GPIO5', owner='power_button'), Claim(resource='GPIO5', owner='gpio_controls')],
    ])
    state = hardware.invoke('get_state')
    assert sorted(state.conflicts) == ['GPIO2', 'GPIO5']
    assert [claim.resource for claim in state.unknown] == ['GPIO99']


def test_pin_options_name_their_users():
    hardware = manager_with(FakeBoard(), [[Claim(resource='GPIO5', owner='gpio_controls', purpose='button next')]])
    options = {choice.value: choice.label for choice in hardware.invoke('pin_options')}
    assert set(options) == {'GPIO2', 'GPIO3', 'GPIO5'}
    assert options['GPIO5'] == 'GPIO5 (pin 29) – gpio_controls: button next'


def test_gpio_line_and_power_go_to_the_board():
    board = FakeBoard()
    hardware = manager_with(board)
    assert hardware.invoke('gpio_line', '5').model_dump() == {'chip': 0, 'line': 5}
    hardware.invoke('shutdown')
    hardware.invoke('reboot')
    assert board.calls == ['shutdown', 'reboot']
    with pytest.raises(OperationError) as error:
        hardware.invoke('gpio_line', '42')
    assert error.value.status == 404


def test_without_a_board():
    hardware = manager_with(None, [[Claim(resource='GPIO5', owner='x')]])
    state = hardware.invoke('get_state')
    assert state.board is None and state.pins == [] and len(state.unknown) == 1
    with pytest.raises(OperationError) as error:
        hardware.invoke('shutdown')
    assert error.value.status == 501
