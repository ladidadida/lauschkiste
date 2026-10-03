import pytest

from lauschkiste.contract.settings import current_values
from lauschkiste.core_modules import CORE_MODULES
from lauschkiste_plugin_mpd import Mpd
from lauschkiste_plugin_raspberry_pi import RaspberryPi

MODULES = [m for m in CORE_MODULES if m.settings is not None] + [Mpd, RaspberryPi]


@pytest.mark.parametrize('module', MODULES, ids=lambda m: m.name)
def test_settings_models_have_valid_defaults_and_schema(module):
    defaults = module.settings().model_dump(mode='json')
    assert current_values(module.settings, {}) == defaults
    schema = module.settings.model_json_schema()
    assert set(schema['properties']) == set(module.settings.model_fields)


def test_invalid_entries_fall_back_to_defaults():
    from lauschkiste.volume import Volume
    values = current_values(Volume.settings, {'soft_max_volume': 300, 'mixer': 'pulse', 'outputs': {'x': {}}})
    assert values == {'mixer': 'pulse', 'startup_volume': None, 'soft_max_volume': 100}


def test_gpio_example_of_the_docs_is_valid():
    values = current_values(RaspberryPi.settings, {'gpio': {
        'enabled': True,
        'buttons': {
            'next': {'pin': 5, 'on_press': {'action': 'player.next'}},
            'play': {'pin': 6, 'on_press': {'action': 'player.toggle'},
                     'on_hold': {'action': 'raspberry_pi.shutdown'}, 'hold_time': 3},
        },
        'rotary_encoders': {'volume': {'pin_a': 17, 'pin_b': 27,
                                       'clockwise': {'action': 'volume.change_volume', 'args': {'step': 2}}}},
        'status_led': 25,
    }})
    assert values['gpio']['buttons']['play']['on_hold'] == {'action': 'raspberry_pi.shutdown', 'args': {}}
    assert values['gpio']['rotary_encoders']['volume']['clockwise']['args'] == {'step': 2}
