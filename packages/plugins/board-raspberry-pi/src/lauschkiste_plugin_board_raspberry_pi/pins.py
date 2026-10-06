"""The 40-pin header of Raspberry Pi models since the B+ (BCM numbering)."""

from pathlib import Path
from typing import Any, Dict, List, Optional

# Header position -> BCM GPIO number
GPIO_AT = {
    3: 2, 5: 3, 7: 4, 8: 14, 10: 15, 11: 17, 12: 18, 13: 27, 15: 22, 16: 23, 18: 24, 19: 10, 21: 9, 22: 25,
    23: 11, 24: 8, 26: 7, 27: 0, 28: 1, 29: 5, 31: 6, 32: 12, 33: 13, 35: 19, 36: 16, 37: 26, 38: 20, 40: 21,
}
POWER_AT = {1: '3V3', 17: '3V3', 2: '5V', 4: '5V', 6: 'GND', 9: 'GND', 14: 'GND', 20: 'GND', 25: 'GND', 30: 'GND',
            34: 'GND', 39: 'GND'}

FUNCTIONS = {
    0: ['id_eeprom.sda'], 1: ['id_eeprom.scl'],
    2: ['i2c1.sda'], 3: ['i2c1.scl'], 4: ['gpclk0'],
    7: ['spi0.ce1'], 8: ['spi0.ce0'], 9: ['spi0.miso'], 10: ['spi0.mosi'], 11: ['spi0.sclk'],
    14: ['uart.tx'], 15: ['uart.rx'],
    18: ['i2s.bclk'], 19: ['i2s.lrclk'], 20: ['i2s.din'], 21: ['i2s.dout'],
}

INTERFACES = [
    {'id': 'i2c1', 'label': 'I²C 1', 'pins': ['GPIO2', 'GPIO3']},
    {'id': 'spi0', 'label': 'SPI 0', 'pins': ['GPIO7', 'GPIO8', 'GPIO9', 'GPIO10', 'GPIO11']},
    {'id': 'i2s', 'label': 'I²S (sound)', 'pins': ['GPIO18', 'GPIO19', 'GPIO21']},
    {'id': 'uart', 'label': 'UART', 'pins': ['GPIO14', 'GPIO15']},
]


def pins() -> List[Dict[str, Any]]:
    result = []
    for position in range(1, 41):
        if position in GPIO_AT:
            bcm = GPIO_AT[position]
            result.append({'id': f'GPIO{bcm}', 'label': f'GPIO{bcm} (pin {position})', 'position': position,
                           'functions': ['gpio', *FUNCTIONS.get(bcm, [])]})
        else:
            name = POWER_AT[position]
            result.append({'id': f'{name}@{position}', 'label': f'{name} (pin {position})', 'position': position,
                           'functions': ['ground' if name == 'GND' else 'power']})
    return result


def pin_id(value: Any) -> Optional[str]:
    """``17``, ``'17'``, ``'GPIO17'``, ``'BCM17'`` -> ``'GPIO17'``; ``'pin11'`` (header position) too."""
    text = str(value).strip().upper()
    if text.startswith('PIN'):
        position = text[3:].strip()
        return f'GPIO{GPIO_AT[int(position)]}' if position.isdigit() and int(position) in GPIO_AT else None
    for prefix in ('GPIO', 'BCM'):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return f'GPIO{int(text)}' if text.isdigit() and int(text) in GPIO_AT.values() else None


def model() -> Optional[str]:
    try:
        return Path('/proc/device-tree/model').read_text().strip('\x00\n ') or None
    except OSError:
        return None


def gpio_chip(model_name: Optional[str]) -> int:
    """The gpiochip of the header: the RP1 chip on a Pi 5 (gpiochip4 on older kernels), else 0."""
    if model_name and 'Pi 5' in model_name and Path('/dev/gpiochip4').exists():
        return 4
    return 0
