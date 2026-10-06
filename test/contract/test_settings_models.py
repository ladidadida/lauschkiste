import pytest

from lauschkiste.contract.settings import current_values
from lauschkiste.core_modules import CORE_MODULES
from lauschkiste_plugin_mpd import Mpd
from lauschkiste_plugin_board_raspberry_pi import BoardRaspberryPi
from lauschkiste_plugin_devices.battery import Battery
from lauschkiste_plugin_devices.gpio_controls import GpioControls
from lauschkiste_plugin_devices.phat_beat import PhatBeat
from lauschkiste_plugin_devices.power_button import PowerButton

MODULES = [m for m in CORE_MODULES if m.settings is not None] + [Mpd, BoardRaspberryPi, Battery, GpioControls,
                                                                    PowerButton, PhatBeat]


@pytest.mark.parametrize('module', MODULES, ids=lambda m: m.name)
def test_settings_models_have_valid_defaults_and_schema(module):
    defaults = module.settings().model_dump(mode='json')
    assert current_values(module.settings, {}) == defaults
    schema = module.settings.model_json_schema()
    assert set(schema['properties']) == set(module.settings.model_fields)


def test_invalid_entries_fall_back_to_defaults():
    from lauschkiste.volume import Volume
    values = current_values(Volume.settings, {'soft_max_volume': 300, 'mixer': 'pulse', 'unknown': 1})
    assert values == {'mixer': 'pulse', 'startup_volume': None, 'soft_max_volume': 100, 'outputs': {}}


def test_gpio_example_of_the_docs_is_valid():
    values = current_values(GpioControls.settings, {
        'buttons': {
            'next': {'pin': 5, 'on_press': {'action': 'player.next'}},
            'play': {'pin': 'GPIO6', 'on_press': {'action': 'player.toggle'},
                     'on_hold': {'action': 'hardware.shutdown'}, 'hold_time': 3},
        },
        'rotary_encoders': {'volume': {'pin_a': 17, 'pin_b': 27,
                                       'clockwise': {'action': 'volume.change_volume', 'args': {'step': 2}}}},
        'status_led': 25,
    })
    assert values['buttons']['next']['pin'] == '5'
    assert values['buttons']['play']['on_hold'] == {'action': 'hardware.shutdown', 'args': {}}
    assert values['rotary_encoders']['volume']['clockwise']['args'] == {'step': 2}
    assert values['status_led'] == '25'


def test_reader_settings_keep_driver_and_wiring():
    from lauschkiste.rfid.reader import Rfid
    reader = {'module': 'rc522_spi', 'config': {'pin_irq': 24}, 'same_id_delay': 2,
              'place_not_swipe': {'enabled': True, 'card_removal_action': {'action': 'player.pause'}}}
    values = current_values(Rfid.settings, {'readers': {'read_00': reader}})
    assert values['readers']['read_00']['config'] == {'pin_irq': 24}
    assert values['readers']['read_00']['place_not_swipe']['card_removal_action']['action'] == 'player.pause'
    assert Rfid.settings.model_json_schema()['properties']['readers']['fixed_keys'] is True
