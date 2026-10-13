import pytest

from lauschkiste_plugin_device_raspberry_pi import hat
from lauschkiste_plugin_device_raspberry_pi.hat import read_hat


def reader(vendor, product):
    files = {hat.HAT_DIR + 'vendor': vendor, hat.HAT_DIR + 'product': product}
    return lambda path: files.get(path)


@pytest.mark.parametrize('product, card', [
    ('DAC+', 'hifiberry-dacplus'), ('DAC+ Pro', 'hifiberry-dacplus'), ('Amp2', 'hifiberry-dacplus'),
    ('DAC2 HD', 'hifiberry-dacplushd'), ('DAC+ ADC', 'hifiberry-dacplusadc'),
    ('DAC+ ADC Pro', 'hifiberry-dacplusadcpro'), ('Digi+', 'hifiberry-digi'), ('Digi+ Pro', 'hifiberry-digi-pro'),
    ('Something', None),
])
def test_hifiberry_products_map_to_their_sound_card(product, card):
    found = read_hat(reader('HiFiBerry\x00', product + '\x00'))
    assert found.sound_card == card and found.label == f'HiFiBerry {product}'


def test_no_hat_or_a_foreign_board():
    assert read_hat(lambda path: None) is None
    other = read_hat(reader('Pimoroni', 'pHAT BEAT'))
    assert other is not None and other.sound_card is None
